"""
================================================================================
Orders Routes - FastAPI Endpoints
================================================================================
Version: 1.0.0
Created: 2025-12-07

Description:
    API routes for B2C Orders module
    - Order management (list, get, update status)
    - WooCommerce webhook handler
    - Manual sync trigger
    - Order statistics
    - Export orders to Excel

Endpoints:
    GET    /orders           - List orders with filtering
    GET    /orders/stats     - Get order statistics
    GET    /orders/{id}      - Get single order by ID
    PUT    /orders/{id}/status - Update order status
    POST   /orders/webhook   - WooCommerce webhook handler
    POST   /orders/sync      - Trigger manual sync from WooCommerce
    POST   /orders/export    - Export orders to Excel

Authentication:
    - Most endpoints require valid JWT token
    - Webhook endpoint is public with HMAC signature validation

================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict
import pandas as pd
from io import BytesIO
from datetime import datetime
import logging
import json

from app.auth.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.orders import (
    OrderResponse,
    OrderListResponse,
    OrderStatsResponse,
    OrderUpdate,
    WooCommerceWebhookPayload,
    WebhookValidationResponse,
    SyncOrdersRequest,
    SyncOrdersResponse,
    OrderExportRequest
)
from app.services.orders_service import OrdersService
from app.database import fetch_one, execute_query

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Order CRUD Endpoints
# ============================================================================

@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List orders with filtering and pagination

    - **status**: Filter by order status (pending, processing, completed, etc.)
    - **customer_id**: Filter by customer ID
    - **start_date**: Filter orders from this date
    - **end_date**: Filter orders up to this date
    - **page**: Page number (starts at 1)
    - **limit**: Number of orders per page (max 1000)
    """
    try:
        offset = (page - 1) * limit

        orders = await OrdersService.get_orders(
            status=status,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Get total count for pagination
        total = await OrdersService.count_orders(
            status=status,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )

        return OrderListResponse(
            orders=orders,
            total=total,
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Error listing orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get order statistics

    Returns:
    - Total orders
    - Orders by status (pending, processing, completed, cancelled)
    - Total revenue
    - Average order value
    """
    try:
        stats = await OrdersService.get_order_stats()
        return OrderStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error fetching order stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order statistics"
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get single order by ID

    Returns order details including line items
    """
    try:
        order = await OrdersService.get_order_by_id(order_id, include_items=True)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )

        return order

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order"
        )


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: OrderUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update order status

    - **status**: New status value (pending, processing, on-hold, completed, cancelled, refunded, failed)
    """
    try:
        if not status_update.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status field is required"
            )

        order = await OrdersService.update_order_status(order_id, status_update.status)

        # Log activity
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            current_user.id,
            'order_status_update',
            'orders',
            f"Updated order {order_id} status to {status_update.status}",
            json.dumps({
                'order_id': order_id,
                'new_status': status_update.status
            })
        )

        return order

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating order status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


# ============================================================================
# Webhook Endpoint
# ============================================================================

@router.post("/webhook", response_model=WebhookValidationResponse)
async def woocommerce_webhook(request: Request):
    """
    WooCommerce webhook handler for order.created and order.updated events

    This endpoint is public but validates HMAC-SHA256 signature from WooCommerce

    Headers required:
    - X-WC-Webhook-Signature: HMAC-SHA256 signature
    - X-WC-Webhook-Source: WooCommerce site URL
    - X-WC-Webhook-Topic: order.created or order.updated
    """
    try:
        # Get headers
        signature = request.headers.get('X-WC-Webhook-Signature')
        topic = request.headers.get('X-WC-Webhook-Topic')
        source = request.headers.get('X-WC-Webhook-Source')

        logger.info(f"Received webhook: topic={topic}, source={source}")

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )

        # Get raw body for signature validation
        body = await request.body()

        # Get webhook secret from settings
        secret_row = await fetch_one(
            "SELECT setting_value FROM system_settings WHERE setting_key = 'woocommerce.webhook_secret'"
        )

        if not secret_row or not secret_row['setting_value']:
            logger.error("WooCommerce webhook secret not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured"
            )

        # Extract and parse webhook secret (handle JSONB encoding)
        webhook_secret = secret_row['setting_value']

        # Handle potential JSON string encoding
        if isinstance(webhook_secret, str) and webhook_secret.startswith('"') and webhook_secret.endswith('"'):
            webhook_secret = json.loads(webhook_secret)

        webhook_secret = str(webhook_secret)

        # Validate signature
        is_valid = await OrdersService.validate_webhook_signature(
            body,
            signature,
            webhook_secret
        )

        if not is_valid:
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Parse JSON payload
        try:
            payload_data = json.loads(body)
            payload = WooCommerceWebhookPayload(**payload_data)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload"
            )

        # Process webhook
        success, message, order_id = await OrdersService.process_webhook(payload, sync_source="webhook")

        if success:
            return WebhookValidationResponse(
                valid=True,
                message=message,
                order_id=order_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


# ============================================================================
# Sync Endpoint
# ============================================================================

@router.post("/sync", response_model=SyncOrdersResponse)
async def sync_orders(
    sync_request: SyncOrdersRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Manually trigger order sync from WooCommerce

    - **days**: Number of days to sync (1-90, default 3)
    - **force_full_sync**: Force sync of all orders (default false)

    This will fetch orders from WooCommerce API and upsert them into the database
    """
    try:
        logger.info(f"Manual sync triggered by user {current_user.id}: {sync_request.days} days")

        # Perform sync
        result = await OrdersService.sync_orders_from_woocommerce(
            days=sync_request.days,
            force_full_sync=sync_request.force_full_sync
        )

        # Log activity
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            current_user.id,
            'order_sync',
            'orders',
            f"Synced {result.synced} orders from WooCommerce ({result.created} created, {result.updated} updated)",
            json.dumps({
                'days': sync_request.days,
                'synced': result.synced,
                'created': result.created,
                'updated': result.updated,
                'errors': result.errors,
                'duration_seconds': result.sync_duration_seconds
            })
        )

        return result

    except Exception as e:
        logger.error(f"Error during manual sync: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync orders: {str(e)}"
        )


# ============================================================================
# Export Endpoint
# ============================================================================

@router.post("/export")
async def export_orders(
    export_request: OrderExportRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Export orders to Excel file

    Filter options:
    - **start_date**: Export orders from this date
    - **end_date**: Export orders up to this date
    - **status**: Filter by status
    - **order_ids**: Export specific order IDs

    Returns Excel file with two sheets:
    - Orders: Full order details
    - Item Summary: Aggregated item quantities
    """
    try:
        # Fetch orders based on filters
        if export_request.order_ids:
            # Fetch specific orders
            orders = []
            for order_id in export_request.order_ids:
                order = await OrdersService.get_order_by_id(order_id, include_items=True)
                if order:
                    orders.append(order)
        else:
            # Fetch orders by date/status filter
            orders = await OrdersService.get_orders(
                status=export_request.status,
                start_date=export_request.start_date,
                end_date=export_request.end_date,
                limit=10000  # Large limit for export
            )

            # Fetch line items for each order
            for order in orders:
                order_details = await OrdersService.get_order_by_id(order['id'], include_items=True)
                order['line_items'] = order_details.get('line_items', [])

        if not orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No orders found matching criteria"
            )

        # Generate Excel file
        excel_data = _generate_excel_export(orders)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"orders_export_{timestamp}.xlsx"

        # Log activity
        await execute_query(
            """
            INSERT INTO activity_logs (user_id, action_type, module_key, description, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            current_user.id,
            'order_export',
            'orders',
            f"Exported {len(orders)} orders to Excel",
            json.dumps({
                'order_count': len(orders),
                'filename': filename
            })
        )

        # Return Excel file
        return StreamingResponse(
            BytesIO(excel_data.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting orders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export orders"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _generate_excel_export(orders: List[Dict]) -> BytesIO:
    """
    Generate Excel file with two sheets: Orders and Item Summary

    Args:
        orders: List of order dictionaries with line_items

    Returns:
        BytesIO object containing Excel file
    """
    output = BytesIO()

    # Process orders into DataFrame
    data = []
    for idx, order in enumerate(sorted(orders, key=lambda x: x.get('id', 0))):
        try:
            # Extract billing info
            billing = order.get('billing', {})
            shipping = order.get('shipping', {})

            # Build customer name
            customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
            if not customer_name:
                customer_name = "Guest"

            # Build shipping address
            shipping_address = ", ".join(filter(None, [
                shipping.get('address_1'),
                shipping.get('address_2'),
                shipping.get('city'),
                shipping.get('state'),
                shipping.get('postcode'),
                shipping.get('country')
            ]))

            # Build items ordered string
            line_items = order.get('line_items', [])
            items_ordered = ", ".join([
                f"{item.get('name', 'Unknown')} x {item.get('quantity', 1)}"
                for item in line_items
            ])

            # Total items
            total_items = sum(item.get('quantity', 1) for item in line_items)

            data.append({
                "S.No": idx + 1,
                "Order ID": order.get('woo_order_id', order.get('id')),
                "Order Number": order.get('order_number', ''),
                "Date": order.get('date_created').strftime('%Y-%m-%d') if order.get('date_created') else '',
                "Status": order.get('status', ''),
                "Customer Name": customer_name,
                "Email": billing.get('email', ''),
                "Phone": billing.get('phone', ''),
                "Items Ordered": items_ordered or 'N/A',
                "Total Items": total_items,
                "Shipping Address": shipping_address or 'N/A',
                "Customer Note": order.get('customer_note', '') or '-',
                "Subtotal": float(order.get('subtotal', 0)),
                "Tax": float(order.get('total_tax', 0)),
                "Shipping": float(order.get('shipping_total', 0)),
                "Discount": float(order.get('discount_total', 0)),
                "Total": float(order.get('total', 0)),
                "Payment Method": order.get('payment_method_title', ''),
                "Transaction ID": order.get('transaction_id', '') or '-',
                "Line Items": line_items
            })

        except Exception as e:
            logger.warning(f"Skipped order {order.get('id')} due to error: {e}")
            continue

    df = pd.DataFrame(data)

    # Create Excel writer
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Orders
        sheet1_df = df.drop(columns=['Line Items']).copy()
        sheet1_df.to_excel(writer, index=False, sheet_name='Orders')

        workbook = writer.book
        worksheet1 = writer.sheets['Orders']

        # Format headers
        header_format = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': '#D3D3D3'})
        for col_num, value in enumerate(sheet1_df.columns.values):
            worksheet1.write(0, col_num, value, header_format)
            worksheet1.set_column(col_num, col_num, 20)

        # Sheet 2: Item Summary
        items_list = []
        for line_items in df['Line Items']:
            for item in line_items:
                items_list.append({
                    'Product ID': item.get('product_id'),
                    'Variation ID': item.get('variation_id'),
                    'SKU': item.get('sku', ''),
                    'Item Name': item.get('name', ''),
                    'Quantity': item.get('quantity', 1)
                })

        if items_list:
            summary_df = pd.DataFrame(items_list)
            summary_df = summary_df.groupby(['Product ID', 'Variation ID', 'SKU', 'Item Name'], as_index=False).sum()
            summary_df = summary_df.sort_values('Quantity', ascending=False)

            summary_df.to_excel(writer, index=False, sheet_name='Item Summary')
            worksheet2 = writer.sheets['Item Summary']

            # Format headers
            for col_num, value in enumerate(summary_df.columns.values):
                worksheet2.write(0, col_num, value, header_format)
                worksheet2.set_column(col_num, col_num, 20)

    output.seek(0)
    return output
