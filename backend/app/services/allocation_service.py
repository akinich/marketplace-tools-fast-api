"""
Allocation Sheet Service
Handles sheet generation, FIFO auto-fill, and cell management
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timezone
from decimal import Decimal
from app.database import fetch_one, fetch_all, execute_query, DatabaseTransaction
import logging
import json

logger = logging.getLogger(__name__)


async def get_or_create_sheet(delivery_date: date) -> int:
    """
    Get existing sheet or create new one for delivery date
    
    Returns:
        sheet_id
    """
    # Check if sheet exists
    existing = await fetch_one(
        "SELECT id FROM allocation_sheets WHERE delivery_date = $1",
        delivery_date
    )
    
    if existing:
        return existing['id']
    
    # Create new sheet
    result = await fetch_one(
        "INSERT INTO allocation_sheets (delivery_date) VALUES ($1) RETURNING id",
        delivery_date
    )
    
    logger.info(f"✅ Created new allocation sheet for {delivery_date}")
    return result['id']


async def generate_sheet_data(delivery_date: date, user_id: str = None) -> Dict[str, Any]:
    """
    Generate complete allocation sheet data for delivery date
    
    Steps:
    1. Get or create sheet record
    2. Query all SOs for delivery date
    3. Generate cells for (item, customer) combinations
    4. Auto-fill SENT quantities using FIFO
    5. Return grid data
    """
    async with DatabaseTransaction() as conn:
        # 1. Get/create sheet
        sheet_id = await get_or_create_sheet(delivery_date)
        
        # 2. Get all SOs for this delivery date
        sos_query = """
            SELECT
                so.id as so_id,
                so.so_number,
                so.customer_id,
                c.contact_name as customer_name,
                soi.item_id,
                soi.quantity
            FROM sales_orders so
            JOIN sales_order_items soi ON so.id = soi.sales_order_id
            JOIN zoho_customers c ON so.customer_id = c.id
            WHERE so.delivery_date = $1
              AND so.status NOT IN ('cancelled', 'delivered')
            ORDER BY so.so_number ASC
        """
        so_items = await conn.fetch(sos_query, delivery_date)
        
        if not so_items:
            logger.warning(f"⚠️ No SOs found for delivery date {delivery_date}")
            return {
                'sheet_id': sheet_id,
                'delivery_date': delivery_date,
                'items': [],
                'customers': [],
                'cells': [],
                'totals': {'total_order': 0, 'total_sent': 0, 'shortfall': 0}
            }
        
        # 3. Get unique items and customers
        item_ids = list(set(item['item_id'] for item in so_items))
        customer_ids = list(set(item['customer_id'] for item in so_items))
        
        # Get item details
        items_query = """
            SELECT id, name, sku
            FROM zoho_items
            WHERE id = ANY($1::int[])
            ORDER BY name
        """
        items = await conn.fetch(items_query, item_ids)
        
        # Get customer details with SO numbers
        customers_dict = {}
        for so_item in so_items:
            cust_id = str(so_item['customer_id'])  # Convert to string to match allocation_sheet_cells.customer_id type
            if cust_id not in customers_dict:
                customers_dict[cust_id] = {
                    'id': cust_id,
                    'name': so_item['customer_name'],
                    'so_number': so_item['so_number'],
                    'so_id': so_item['so_id']
                }

        customers = sorted(customers_dict.values(), key=lambda c: c['so_number'])
        
        # 4. Generate/update cells
        cells = []
        for so_item in so_items:
            # Check if cell exists
            existing_cell = await conn.fetchrow("""
                SELECT * FROM allocation_sheet_cells
                WHERE sheet_id = $1
                  AND item_id = $2
                  AND customer_id = $3
            """, sheet_id, so_item['item_id'], str(so_item['customer_id']))

            if existing_cell:
                # Update ORDER quantity if SO changed
                if existing_cell['order_quantity'] != so_item['quantity']:
                    await conn.execute("""
                        UPDATE allocation_sheet_cells
                        SET order_quantity = $1, updated_at = NOW()
                        WHERE id = $2
                    """, so_item['quantity'], existing_cell['id'])

                cells.append(dict(existing_cell))
            else:
                # Create new cell
                new_cell = await conn.fetchrow("""
                    INSERT INTO allocation_sheet_cells (
                        sheet_id, item_id, customer_id, so_id,
                        order_quantity, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING *
                """, sheet_id, so_item['item_id'], str(so_item['customer_id']),
                    so_item['so_id'], so_item['quantity'], user_id)
                
                cells.append(dict(new_cell))
        
        # 5. Auto-fill SENT quantities using FIFO
        await auto_fill_sent_quantities(sheet_id, conn)
        
        # 6. Reload cells with allocated batches
        cells_query = """
            SELECT * FROM allocation_sheet_cells
            WHERE sheet_id = $1
            ORDER BY item_id, customer_id
        """
        cells = await conn.fetch(cells_query, sheet_id)
        
        # 7. Calculate totals
        total_order = sum(Decimal(str(c['order_quantity'])) for c in cells)
        total_sent = sum(Decimal(str(c['sent_quantity'] or 0)) for c in cells)
        
        return {
            'sheet_id': sheet_id,
            'delivery_date': delivery_date,
            'items': [dict(i) for i in items],
            'customers': customers,
            'cells': [format_cell_response(dict(c)) for c in cells],
            'totals': {
                'total_order': float(total_order),
                'total_sent': float(total_sent),
                'shortfall': float(total_order - total_sent)
            }
        }


async def auto_fill_sent_quantities(sheet_id: int, conn=None):
    """
    Auto-fill SENT quantities using FIFO algorithm
    
    FIFO Priority:
    1. Expiring soon (< 2 days)
    2. Repacked batches (B###R)
    3. Oldest by entry_date
    
    Customer Priority:
    - SO number ascending (lower number = higher priority)
    """
    should_close = False
    if conn is None:
        conn = DatabaseTransaction()
        await conn.__aenter__()
        should_close = True
    
    try:
        # Get all cells for this sheet
        cells = await conn.fetch("""
            SELECT * FROM allocation_sheet_cells
            WHERE sheet_id = $1
            ORDER BY item_id, so_id
        """, sheet_id)
        
        # Group by item
        items_dict = {}
        for cell in cells:
            item_id = cell['item_id']
            if item_id not in items_dict:
                items_dict[item_id] = []
            items_dict[item_id].append(cell)
        
        # Process each item
        for item_id, item_cells in items_dict.items():
            # Get available stock for this item with FIFO priority
            stock_query = """
                SELECT
                    i.id, i.batch_id, i.quantity,
                    b.batch_number, b.is_repacked,
                    i.expiry_date,
                    i.entry_date,
                    CASE 
                        WHEN i.expiry_date IS NOT NULL 
                             AND i.expiry_date <= CURRENT_DATE + INTERVAL '2 days' 
                        THEN TRUE
                        ELSE FALSE
                    END as is_expiring_soon
                FROM inventory i
                JOIN batches b ON i.batch_id = b.id
                WHERE i.item_id = $1
                  AND i.location = 'packed_warehouse'
                  AND i.status = 'available'
                ORDER BY 
                    CASE 
                        WHEN i.expiry_date IS NOT NULL 
                             AND i.expiry_date <= CURRENT_DATE + INTERVAL '2 days' 
                        THEN 0
                        ELSE 1
                    END,
                    b.is_repacked DESC,
                    i.entry_date ASC
            """
            stock = await conn.fetch(stock_query, item_id)
            
            if not stock:
                # No stock available - leave SENT empty
                continue
            
            # Convert to mutable list of dicts
            remaining_stock = [dict(s) for s in stock]
            
            # Allocate to customers (already sorted by SO number via ORDER BY)
            for cell in item_cells:
                needed = Decimal(str(cell['order_quantity']))
                allocated = []
                allocated_qty = Decimal('0')
                
                for batch in remaining_stock[:]:  # Create copy for iteration
                    if allocated_qty >= needed:
                        break
                    
                    batch_qty = Decimal(str(batch['quantity']))
                    take = min(batch_qty, needed - allocated_qty)
                    
                    allocated.append({
                        'batch_id': batch['batch_id'],
                        'batch_number': batch['batch_number'],
                        'quantity': float(take),
                        'is_repacked': batch['is_repacked'],
                        'is_expiring_soon': batch['is_expiring_soon']
                    })
                    
                    allocated_qty += take
                    batch['quantity'] = float(batch_qty - take)
                    
                    # Remove exhausted batches
                    if batch['quantity'] <= 0:
                        remaining_stock.remove(batch)
                
                # Update cell with allocated quantity and batches
                await conn.execute("""
                    UPDATE allocation_sheet_cells
                    SET sent_quantity = $1,
                        allocated_batches = $2::jsonb,
                        updated_at = NOW()
                    WHERE id = $3
                """, float(allocated_qty), json.dumps(allocated), cell['id'])
        
        logger.info(f"✅ Auto-filled SENT quantities for sheet {sheet_id}")
        
    finally:
        if should_close:
            await conn.__aexit__(None, None, None)


def format_cell_response(cell: Dict) -> Dict[str, Any]:
    """Format cell for API response"""
    sent = Decimal(str(cell.get('sent_quantity') or 0))
    ordered = Decimal(str(cell['order_quantity']))
    
    return {
        'id': cell['id'],
        'sheet_id': cell['sheet_id'],
        'item_id': cell['item_id'],
        'customer_id': cell['customer_id'],
        'so_id': cell['so_id'],
        'order_quantity': float(ordered),
        'sent_quantity': float(sent) if sent > 0 else None,
        'order_modified': cell['order_modified'],
        'invoice_status': cell['invoice_status'],
        'invoice_id': cell.get('invoice_id'),
        'allocated_batches': cell.get('allocated_batches'),
        'has_shortfall': sent < ordered,
        'version': cell['version'],
        'created_at': cell['created_at'].isoformat(),
        'updated_at': cell['updated_at'].isoformat()
    }


async def update_cell(
    cell_id: int,
    order_quantity: Optional[Decimal] = None,
    sent_quantity: Optional[Decimal] = None,
    version: int = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Update cell with optimistic locking
    
    Returns:
        Updated cell + metadata about what changed
    """
    async with DatabaseTransaction() as conn:
        # Get current cell
        cell = await conn.fetchrow(
            "SELECT * FROM allocation_sheet_cells WHERE id = $1",
            cell_id
        )
        
        if not cell:
            raise ValueError(f"Cell {cell_id} not found")
        
        # Check version (optimistic locking)
        if version is not None and cell['version'] != version:
            raise ValueError(
                f"Version conflict: expected {version}, got {cell['version']}. "
                "Cell was modified by another user."
            )
        
        updated_so = False
        recalculated_batches = False
        
        # Update ORDER quantity
        if order_quantity is not None:
            await conn.execute("""
                UPDATE allocation_sheet_cells
                SET order_quantity = $1,
                    order_modified = TRUE,
                    updated_at = NOW()
                WHERE id = $2
            """, float(order_quantity), cell_id)
            
            # Update SO
            await conn.execute("""
                UPDATE sales_order_items
                SET quantity = $1
                WHERE sales_order_id = $2 AND item_id = $3
            """, float(order_quantity), cell['so_id'], cell['item_id'])
            
            updated_so = True
        
        # Update SENT quantity
        if sent_quantity is not None:
            # Recalculate batches for manual sent quantity using FIFO
            item_id_val = await conn.fetchval("""
                SELECT item_id FROM allocation_sheet_cells WHERE id = $1
            """, cell_id)
            
            if item_id_val:
                # Get available batches (same query as auto_fill_sent_quantities)
                batches = await conn.fetch("""
                    SELECT 
                        id as batch_id,
                        batch_number,
                        (quantity - allocated_qty - sold_qty) as available_qty,
                        CASE 
                            WHEN batch_number LIKE '%R' THEN TRUE
                            ELSE FALSE
                        END as is_repacked,
                        CASE 
                            WHEN expiry_date < (CURRENT_DATE + INTERVAL '2 days') THEN TRUE
                            ELSE FALSE
                        END as is_expiring_soon,
                        expiry_date,
                        entry_date
                    FROM inventory_batches
                    WHERE item_id = $1 
                      AND (quantity - allocated_qty - sold_qty) > 0
                    ORDER BY 
                        CASE WHEN expiry_date < (CURRENT_DATE + INTERVAL '2 days') THEN 1 ELSE 2 END,
                        CASE WHEN batch_number LIKE '%R' THEN 2 ELSE 3 END,
                        entry_date ASC
                """, item_id_val)
                
                # Allocate batches
                allocated = []
                allocated_qty = 0
                needed = float(sent_quantity)
                
                for batch in batches:
                    if allocated_qty >= needed:
                        break
                    
                    take = min(batch['available_qty'], needed - allocated_qty)
                    allocated.append({
                        'batch_id': batch['batch_id'],
                        'batch_number': batch['batch_number'],
                        'qty_allocated': float(take),
                        'is_repacked': batch['is_repacked'],
                        'is_expiring_soon': batch['is_expiring_soon']
                    })
                    allocated_qty += float(take)
                
                # Update cell
                await conn.execute("""
                    UPDATE allocation_sheet_cells
                    SET sent_quantity = $1,
                        allocated_batches = $2,
                        has_shortfall = ($1 > $3),
                        invoice_status = 'pending',
                        updated_at = NOW()
                    WHERE id = $4
                """, 
                    float(sent_quantity), 
                    json.dumps(allocated),
                    allocated_qty,
                    cell_id
                )
            else:
                # Fallback
                await conn.execute("""
                    UPDATE allocation_sheet_cells
                    SET sent_quantity = $1,
                        invoice_status = 'pending',
                        updated_at = NOW()
                    WHERE id = $2
                """, float(sent_quantity), cell_id)
            
            recalculated_batches = True
        
        # Reload cell
        updated_cell = await conn.fetchrow(
            "SELECT * FROM allocation_sheet_cells WHERE id = $1",
            cell_id
        )
        
        return {
            'cell': format_cell_response(dict(updated_cell)),
            'updated_so': updated_so,
            'recalculated_batches': recalculated_batches,
            'conflicts': []
        }
