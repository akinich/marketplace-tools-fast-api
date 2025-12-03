"""
================================================================================
Woo to Zoho Export Service
================================================================================
Version: 1.0.0
Created: 2025-12-03

Service for exporting WooCommerce orders to Zoho Books format.
Handles fetching orders, mapping products, generating files, and tracking history.
================================================================================
"""

import logging
import io
import csv
import zipfile
from typing import List, Dict, Any, Tuple, Optional
from datetime import date, datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment

from app.database import fetch_all, fetch_one, execute_query
from app.services.woocommerce_service import WooCommerceService

logger = logging.getLogger(__name__)

class WooToZohoService:
    
    @staticmethod
    async def get_product_mapping() -> Dict[int, Dict[str, str]]:
        """
        Fetch product mapping from database.
        Returns dict: {product_id or variation_id: {'zoho_name', 'hsn', 'usage_units'}}
        """
        try:
            # Fetch active products with mapping info
            query = """
                SELECT product_id, variation_id, zoho_name, hsn, usage_units 
                FROM products 
                WHERE is_active = true
            """
            rows = await fetch_all(query)
            
            mapping = {}
            for row in rows:
                # Use variation_id if exists, otherwise product_id
                key = row['variation_id'] if row['variation_id'] else row['product_id']
                if key:
                    mapping[key] = {
                        'zoho_name': row.get('zoho_name') or '',
                        'hsn': row.get('hsn') or '',
                        'usage_units': row.get('usage_units') or ''
                    }
            return mapping
        except Exception as e:
            logger.error(f"Error fetching product mapping: {e}")
            return {}

    @staticmethod
    async def get_last_sequence(prefix: str) -> Optional[int]:
        """
        Get the last used sequence number for given prefix from export history.
        """
        try:
            query = """
                SELECT sequence_number 
                FROM export_history 
                WHERE invoice_prefix = $1 
                ORDER BY sequence_number DESC 
                LIMIT 1
            """
            row = await fetch_one(query, prefix)
            return row['sequence_number'] if row else None
        except Exception as e:
            logger.error(f"Error fetching last sequence: {e}")
            return None

    @staticmethod
    async def fetch_orders(start_date: date, end_date: date) -> List[Dict]:
        """
        Fetch completed orders from WooCommerce.
        """
        return await WooCommerceService.fetch_orders(start_date, end_date, status="completed")

    @staticmethod
    def _to_float(x) -> float:
        """Convert value to float, return 0.0 if invalid."""
        try:
            if x is None or x == "":
                return 0.0
            return float(x)
        except Exception:
            return 0.0

    @staticmethod
    async def transform_orders(
        orders: List[Dict], 
        product_mapping: Dict, 
        invoice_prefix: str, 
        start_sequence: int
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Transform orders into CSV rows and replacements log.
        Returns: (csv_rows, replacements_log, completed_orders)
        """
        # Sort by ID
        orders.sort(key=lambda x: x.get("id", 0))
        
        csv_rows = []
        replacements_log = []
        sequence_number = start_sequence
        
        for order in orders:
            order_id = order.get("id")
            invoice_number = f"{invoice_prefix}{sequence_number:05d}"
            sequence_number += 1
            
            # Parse date
            date_created = order.get("date_created")
            invoice_date = ""
            if date_created:
                try:
                    dt = datetime.fromisoformat(date_created)
                    invoice_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    invoice_date = str(date_created).split('T')[0]

            billing = order.get('billing', {})
            customer_name = f"{billing.get('first_name','')} {billing.get('last_name','')}".strip()
            place_of_supply = billing.get('state', '')
            currency = order.get('currency', '')
            shipping_charge = WooToZohoService._to_float(order.get('shipping_total', 0))
            entity_discount = WooToZohoService._to_float(order.get('discount_total', 0))

            for item in order.get("line_items", []):
                original_item_name = item.get("name", "")
                variation_id = item.get("variation_id", 0)
                product_id = item.get("product_id", 0)
                
                # Match by variation_id first, then product_id
                lookup_id = variation_id if variation_id else product_id
                
                mapping = product_mapping.get(lookup_id, {})
                
                item_name_final = mapping.get("zoho_name") or original_item_name
                hsn = mapping.get("hsn", "")
                usage_unit = mapping.get("usage_units", "")
                
                # Log replacement if zoho_name used
                if mapping.get("zoho_name"):
                    replacements_log.append({
                        "Product ID": product_id,
                        "Variation ID": variation_id if variation_id else "-",
                        "Original WooCommerce Name": original_item_name,
                        "Replaced Zoho Name": item_name_final,
                        "HSN": hsn,
                        "Usage Unit": usage_unit
                    })
                
                # Fallback to meta data if not mapped
                if not hsn or not usage_unit:
                    for meta in item.get("meta_data", []) or []:
                        key = str(meta.get("key", "")).lower()
                        if key == "hsn" and not hsn:
                            hsn = str(meta.get("value", ""))
                        if key == "usage unit" and not usage_unit:
                            usage_unit = str(meta.get("value", ""))

                # Tax
                try:
                    item_tax_pct = float(item.get("tax_class") or 0)
                except (TypeError, ValueError):
                    item_tax_pct = 0.0

                # HSN formatting for Excel (prevent leading zero stripping)
                hsn_formatted = f"'{hsn}" if hsn else ""

                quantity = item.get("quantity", 0)
                subtotal = WooToZohoService._to_float(item.get("subtotal", 0))
                unit_price = subtotal / quantity if quantity > 0 else 0.0

                row = {
                    "Invoice Number": invoice_number,
                    "PurchaseOrder": order_id,
                    "Invoice Date": invoice_date,
                    "Invoice Status": str(order.get("status", "")).capitalize(),
                    "Customer Name": customer_name,
                    "Place of Supply": place_of_supply,
                    "Currency Code": currency,
                    "Item Name": item_name_final,
                    "HSN/SAC": hsn_formatted,
                    "Item Type": "goods", # Default
                    "Quantity": quantity,
                    "Usage unit": usage_unit,
                    "Item Price": unit_price,
                    "Is Inclusive Tax": "FALSE",
                    "Item Tax %": item_tax_pct,
                    "Discount Type": "entity_level",
                    "Is Discount Before Tax": "TRUE",
                    "Entity Discount Amount": entity_discount,
                    "Shipping Charge": shipping_charge,
                    "Item Tax Exemption Reason": "ITEM EXEMPT FROM GST",
                    "Supply Type": "Exempted",
                    "GST Treatment": "consumer"
                }
                csv_rows.append(row)
                
        return csv_rows, replacements_log, orders

    @staticmethod
    def generate_files(
        csv_rows: List[Dict], 
        orders: List[Dict], 
        invoice_prefix: str, 
        start_sequence: int,
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Generate ZIP file containing CSV and Excel summary.
        """
        # 1. Create CSV
        df_csv = pd.DataFrame(csv_rows)
        csv_buffer = io.StringIO()
        df_csv.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode('utf-8')

        # 2. Create Excel Summary
        # Calculate summary metrics
        total_orders = len(orders)
        total_revenue = 0.0
        
        order_details_rows = []
        seq_temp = start_sequence
        
        for order in orders:
            order_total = WooToZohoService._to_float(order.get("total", 0))
            refunds = order.get("refunds") or []
            refund_total = sum(WooToZohoService._to_float(r.get("amount") or r.get("total") or 0) for r in refunds)
            net_total = order_total - refund_total
            total_revenue += net_total
            
            invoice_number = f"{invoice_prefix}{seq_temp:05d}"
            seq_temp += 1
            
            # Date formatting
            date_created = order.get("date_created")
            order_date = ""
            if date_created:
                try:
                    dt = datetime.fromisoformat(date_created)
                    order_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    order_date = str(date_created).split('T')[0]
            
            billing = order.get('billing', {})
            customer_name = f"{billing.get('first_name','')} {billing.get('last_name','')}".strip()

            order_details_rows.append({
                "Invoice Number": invoice_number,
                "Order Number": order.get("id"),
                "Date": order_date,
                "Customer Name": customer_name,
                "Order Total": net_total
            })

        first_order_id = orders[0].get("id") if orders else ""
        last_order_id = orders[-1].get("id") if orders else ""
        first_inv = f"{invoice_prefix}{start_sequence:05d}"
        last_inv = f"{invoice_prefix}{(start_sequence + total_orders - 1):05d}" if orders else ""

        summary_data = {
            "Metric": [
                "Total Orders Fetched",
                "Completed Orders",
                "Total Revenue (Net of Refunds)",
                "Completed Order ID Range",
                "Invoice Number Range"
            ],
            "Value": [
                total_orders,
                total_orders,
                total_revenue,
                f"{first_order_id} -> {last_order_id}",
                f"{first_inv} -> {last_inv}"
            ]
        }
        
        df_summary = pd.DataFrame(summary_data)
        df_details = pd.DataFrame(order_details_rows)
        
        # Add grand total
        if not df_details.empty:
            grand_total = df_details["Order Total"].sum()
            grand_total_row = pd.DataFrame([{
                "Invoice Number": "Grand Total",
                "Order Number": "",
                "Date": "",
                "Customer Name": "",
                "Order Total": grand_total
            }])
            df_details = pd.concat([df_details, grand_total_row], ignore_index=True)

        # Write Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_summary.to_excel(writer, index=False, sheet_name="Summary Metrics")
            df_details.to_excel(writer, index=False, sheet_name="Order Details")
            
            # Formatting
            for sheet_name in writer.sheets:
                ws = writer.sheets[sheet_name]
                # Header bold
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center")
                # Auto width
                for col in ws.columns:
                    max_length = 0
                    column = col[0].column_letter # Get the column name
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    ws.column_dimensions[column].width = adjusted_width

        excel_bytes = excel_buffer.getvalue()

        # 3. Zip it
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            date_str = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            zf.writestr(f"orders_{date_str}.csv", csv_bytes)
            zf.writestr(f"summary_report_{date_str}.xlsx", excel_bytes)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @staticmethod
    async def save_history(
        orders: List[Dict],
        invoice_prefix: str,
        start_sequence: int,
        start_date: date,
        end_date: date,
        user_id: str
    ):
        """Save export history to database."""
        try:
            seq = start_sequence
            
            # Prepare batch insert
            # Note: asyncpg supports executemany but we need to construct the query
            # For simplicity and safety, we'll loop or use a bulk insert query construction
            # Given the number of orders might be 100-200, a loop is okay-ish but bulk is better.
            # Let's use a loop for now as it's safer with error handling, or construct a large INSERT.
            
            values = []
            for order in orders:
                invoice_number = f"{invoice_prefix}{seq:05d}"
                order_total = WooToZohoService._to_float(order.get("total", 0))
                refunds = order.get("refunds") or []
                refund_total = sum(WooToZohoService._to_float(r.get("amount") or r.get("total") or 0) for r in refunds)
                net_total = order_total - refund_total
                
                billing = order.get('billing', {})
                customer_name = f"{billing.get('first_name','')} {billing.get('last_name','')}".strip()
                
                # Parse date
                date_created = order.get("date_created")
                order_dt = None
                if date_created:
                    try:
                        order_dt = datetime.fromisoformat(date_created)
                    except ValueError:
                        pass

                values.append((
                    invoice_number,
                    invoice_prefix,
                    seq,
                    order.get('id'),
                    order_dt,
                    customer_name,
                    net_total,
                    start_date,
                    end_date,
                    len(orders),
                    user_id
                ))
                seq += 1

            # Bulk insert query
            query = """
                INSERT INTO export_history (
                    invoice_number, invoice_prefix, sequence_number, order_id, 
                    order_date, customer_name, order_total, 
                    date_range_start, date_range_end, total_orders_in_export, exported_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
            
            # We need to execute this for each row. 
            # app.database.execute_query runs fetchval/execute.
            # We can't easily access executemany via the helper.
            # So we'll iterate.
            for v in values:
                await execute_query(query, *v)
                
            logger.info(f"Saved {len(values)} export history records")
            return True
            
        except Exception as e:
            logger.error(f"Error saving history: {e}")
            return False

    @staticmethod
    async def get_history(start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Dict]:
        """Fetch export history."""
        try:
            query = """
                SELECT
                    h.*,
                    u.email as exported_by_email
                FROM export_history h
                LEFT JOIN auth.users u ON h.exported_by = u.id
                WHERE 1=1
            """
            params = []
            if start_date:
                params.append(start_date)
                query += f" AND h.date_range_start >= ${len(params)}"
            if end_date:
                params.append(end_date)
                query += f" AND h.date_range_end <= ${len(params)}"

            query += " ORDER BY h.created_at DESC LIMIT 1000"

            rows = await fetch_all(query, *params)

            # Convert UUID to string for Pydantic validation
            result = []
            for row in rows:
                row_dict = dict(row)
                if row_dict.get('exported_by'):
                    row_dict['exported_by'] = str(row_dict['exported_by'])
                result.append(row_dict)

            return result
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []
