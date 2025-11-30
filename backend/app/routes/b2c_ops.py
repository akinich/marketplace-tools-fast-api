"""
================================================================================
B2C Operations Routes - FastAPI Endpoints
================================================================================
Version: 1.0.0
Created: 2025-11-30

Description:
    API routes for B2C Operations module
    - Order Extractor: Fetch and export WooCommerce orders

Endpoints:
    POST /b2c-ops/orders/fetch - Fetch orders from WooCommerce
    POST /b2c-ops/orders/export - Export selected orders to Excel

Authentication:
    - Requires valid JWT token
    - Requires 'order_extractor' module access

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List
import pandas as pd
from io import BytesIO
from datetime import datetime
import logging

from app.auth.dependencies import get_current_user, require_module_access
from app.schemas.auth import CurrentUser
from app.schemas.b2c_ops import (
    OrderFetchRequest,
    OrderFetchResponse,
    OrderExportRequest,
    WooCommerceOrder
)
from app.services.woocommerce_service import WooCommerceService
from app.database import fetch_one, execute_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/b2c-ops", tags=["B2C Operations"])


# ============================================================================
# Order Extractor Endpoints
# ============================================================================

@router.post("/orders/fetch", response_model=OrderFetchResponse)
async def fetch_orders(
    request: OrderFetchRequest,
    current_user: CurrentUser = Depends(require_module_access("order_extractor"))
):
    """
    Fetch orders from WooCommerce between specified dates
    
    - **start_date**: Start date for order fetching (YYYY-MM-DD)
    - **end_date**: End date for order fetching (YYYY-MM-DD, max 31 days from start)
    
    Returns list of orders with customer details, line items, and totals
    """
    try:
        # Fetch orders from WooCommerce
        orders = await WooCommerceService.fetch_orders(
            request.start_date,
            request.end_date
        )
        
        # Log activity
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            current_user.id,
            'order_fetch',
            'order_extractor',
            f"Fetched {len(orders)} orders from {request.start_date} to {request.end_date}",
            {
                'start_date': str(request.start_date),
                'end_date': str(request.end_date),
                'order_count': len(orders)
            }
        )
        
        return OrderFetchResponse(
            orders=orders,
            total_count=len(orders),
            start_date=str(request.start_date),
            end_date=str(request.end_date)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch orders. Please try again or contact support."
        )


@router.post("/orders/export")
async def export_orders(
    request: OrderExportRequest,
    current_user: CurrentUser = Depends(require_module_access("order_extractor"))
):
    """
    Export selected orders to Excel file
    
    - **order_ids**: List of order IDs to export
    - **start_date**: Start date for filename
    - **end_date**: End date for filename
    
    Returns Excel file with two sheets:
    - Orders: Customer details and order information
    - Item Summary: Aggregated item quantities
    """
    try:
        # Get API credentials
        api_url, consumer_key, consumer_secret = await WooCommerceService.get_api_credentials()
        
        # Fetch the selected orders
        import httpx
        client = httpx.Client(
            auth=(consumer_key, consumer_secret),
            timeout=30.0
        )
        
        orders = []
        for order_id in request.order_ids:
            try:
                response = client.get(f"{api_url}/orders/{order_id}")
                if response.status_code == 200:
                    orders.append(response.json())
            except Exception as e:
                logger.warning(f"Failed to fetch order {order_id}: {str(e)}")
                continue
        
        client.close()
        
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No orders found for the provided IDs"
            )
        
        # Generate Excel file
        excel_data = _generate_excel(orders)
        
        # Log activity
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            current_user.id,
            'order_download',
            'order_extractor',
            f"Downloaded {len(orders)} orders from {request.start_date} to {request.end_date}",
            {
                'start_date': str(request.start_date),
                'end_date': str(request.end_date),
                'order_count': len(orders),
                'order_ids': request.order_ids
            }
        )
        
        # Generate filename
        filename = f"orders_{request.start_date.strftime('%Y%m%d')}_{request.end_date.strftime('%Y%m%d')}.xlsx"
        
        # Return Excel file as streaming response
        return StreamingResponse(
            BytesIO(excel_data.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting orders: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to export orders. Please try again or contact support."
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _generate_excel(orders: List[dict]) -> BytesIO:
    """
    Generate Excel file with two sheets: Orders and Item Summary
    
    Args:
        orders: List of WooCommerce order dictionaries
        
    Returns:
        BytesIO object containing Excel file
    """
    output = BytesIO()
    
    # Process orders into DataFrame
    data = []
    for idx, order in enumerate(sorted(orders, key=lambda x: x.get('id', 0))):
        try:
            # Safely get order data
            order_id = order.get('id', 'N/A')
            date_created = order.get('date_created', '')
            
            # Parse date
            try:
                order_date = datetime.strptime(date_created, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
            except:
                order_date = date_created[:10] if date_created else 'N/A'
            
            # Build Items Ordered with quantities
            line_items = order.get('line_items', [])
            items_ordered = ", ".join([
                f"{item.get('name', 'Unknown')} x {item.get('quantity', 1)}" 
                for item in line_items
            ])
            
            # Total items
            total_items = sum(item.get('quantity', 1) for item in line_items)
            
            # Shipping address
            shipping = order.get("shipping", {})
            shipping_address = ", ".join(filter(None, [
                shipping.get("address_1"),
                shipping.get("address_2"),
                shipping.get("city"),
                shipping.get("state"),
                shipping.get("postcode"),
                shipping.get("country")
            ]))
            
            # Billing info
            billing = order.get('billing', {})
            full_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
            if not full_name:
                full_name = "N/A"
            
            # Customer notes
            customer_notes = order.get('customer_note', '').strip()
            if not customer_notes:
                customer_notes = "-"
            
            # Transaction ID
            transaction_id = order.get('transaction_id', '')
            if not transaction_id:
                transaction_id = "-"
            
            data.append({
                "S.No": idx + 1,
                "Order ID": order_id,
                "Date": order_date,
                "Name": full_name,
                "Items Ordered": items_ordered if items_ordered else 'N/A',
                "Total Items": total_items,
                "Shipping Address": shipping_address if shipping_address else 'N/A',
                "Mobile Number": billing.get('phone', ''),
                "Customer Notes": customer_notes,
                "Order Value": float(order.get('total', 0)),
                "Payment Method": order.get('payment_method_title', ''),
                "Transaction ID": transaction_id,
                "Order Status": order.get('status', 'unknown'),
                "Line Items": line_items
            })
        except Exception as e:
            logger.warning(f"Skipped order due to data error: {str(e)}")
            continue
    
    df = pd.DataFrame(data)
    
    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Orders
        sheet1_df = df[[
            "S.No", "Order ID", "Name", "Items Ordered", "Total Items",
            "Shipping Address", "Mobile Number", "Customer Notes",
            "Order Value", "Payment Method", "Transaction ID", "Order Status"
        ]].copy()
        
        sheet1_df.rename(columns={
            "Order ID": "Order #",
            "Order Value": "Order Total"
        }, inplace=True)
        
        sheet1_df.to_excel(writer, index=False, sheet_name='Orders')
        workbook = writer.book
        worksheet1 = writer.sheets['Orders']
        
        # Format headers
        header_format = workbook.add_format({'bold': True, 'font_color': 'black'})
        for col_num, value in enumerate(sheet1_df.columns.values):
            worksheet1.write(0, col_num, value, header_format)
            worksheet1.set_column(col_num, col_num, 30)
        
        # Sheet 2: Item Summary
        items_list = []
        for line_items in df['Line Items']:
            for item in line_items:
                items_list.append((
                    item.get('product_id', None),
                    item.get('variation_id', None),
                    item.get('name', ''),
                    item.get('quantity', 1)
                ))
        
        summary_df = pd.DataFrame(items_list, columns=['Item ID', 'Variation ID', 'Item Name', 'Quantity'])
        summary_df = summary_df.groupby(['Item ID', 'Variation ID', 'Item Name'], as_index=False).sum()
        summary_df = summary_df.sort_values(['Item ID', 'Variation ID', 'Item Name'])
        
        summary_df.to_excel(writer, index=False, sheet_name='Item Summary')
        worksheet2 = writer.sheets['Item Summary']
        
        # Format headers
        for col_num, value in enumerate(summary_df.columns.values):
            worksheet2.write(0, col_num, value, header_format)
            worksheet2.set_column(col_num, col_num, 25)
    
    output.seek(0)
    return output
