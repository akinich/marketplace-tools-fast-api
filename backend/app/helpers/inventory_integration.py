"""
================================================================================
Farm Management System - Inventory Integration Helper
================================================================================
Version: 1.0.0
Last Updated: 2025-11-18

Description:
    Helper class for integrating other modules (like biofloc) with the
    inventory module. Provides a clean interface for stock operations,
    reservations, and reporting.

Usage Example:
    inv = InventoryIntegration(module_name="biofloc")

    # Batch deduction for feeding
    result = await inv.batch_deduct(
        deductions=[{"sku": "FEED-PELLET-3MM", "quantity": 5.5}],
        module_reference="biofloc",
        tank_id=str(tank_id),
        batch_id=str(batch_id)
    )

    # Check stock availability
    items = await inv.bulk_fetch(skus=["FEED-PELLET-3MM", "CHEM-PH-DOWN"])

================================================================================
"""

import logging
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID

# Import inventory service functions
from app.services import inventory_service
from app.schemas.inventory import (
    BatchDeductionRequest,
    BatchDeductionItem,
    ModuleType,
    BulkFetchRequest,
    CreateReservationRequest,
    UseStockRequest
)

logger = logging.getLogger(__name__)


class InventoryIntegration:
    """
    Helper class for integrating modules with inventory system.

    Provides simplified methods for:
    - Batch stock deduction (atomic)
    - Bulk item fetching
    - Stock reservations
    - Consumption reporting
    """

    def __init__(self, module_name: str = "biofloc"):
        """
        Initialize inventory integration helper.

        Args:
            module_name: Name of the module using inventory (default: "biofloc")
        """
        self.module_name = module_name
        self.module_ref = ModuleType(module_name.lower())

    # ========================================================================
    # STOCK DEDUCTION
    # ========================================================================

    async def batch_deduct(
        self,
        deductions: List[Dict],
        module_reference: str,
        tank_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        session_number: Optional[int] = None,
        global_notes: Optional[str] = None,
        user_id: str = None,
        username: str = "system"
    ) -> Dict:
        """
        Deduct multiple items atomically (all succeed or all fail).

        Args:
            deductions: List of dicts with {"sku": str, "quantity": float, "notes": str (optional)}
            module_reference: Module name (e.g., "biofloc")
            tank_id: Optional tank/location reference
            batch_id: Optional batch reference from calling module
            session_number: Optional session number for tracking
            global_notes: Notes applied to all transactions
            user_id: User performing the operation
            username: Username for audit trail

        Returns:
            Dict with keys:
                - success: bool
                - total: int (total items)
                - successful: int
                - failed: int
                - total_cost: Decimal
                - results: List[dict] (per-item results)
                - transaction_ids: List[UUID]

        Example:
            result = await inv.batch_deduct(
                deductions=[
                    {"sku": "FEED-PELLET-3MM", "quantity": 5.5},
                    {"sku": "FEED-VITAMIN-MIX", "quantity": 0.2}
                ],
                module_reference="biofloc",
                tank_id="tank-uuid",
                batch_id="batch-uuid",
                session_number=1,
                user_id="user-uuid"
            )
        """
        try:
            # Convert deductions to BatchDeductionItem objects
            deduction_items = []
            for item in deductions:
                deduction_items.append(
                    BatchDeductionItem(
                        sku=item["sku"],
                        quantity=Decimal(str(item["quantity"])),
                        notes=item.get("notes")
                    )
                )

            # Create batch deduction request
            request = BatchDeductionRequest(
                deductions=deduction_items,
                module_reference=ModuleType(module_reference.lower()),
                tank_id=tank_id,
                batch_id=batch_id,
                session_number=session_number,
                global_notes=global_notes
            )

            # Execute batch deduction
            result = await inventory_service.batch_deduct_stock(
                request=request,
                user_id=user_id,
                username=username
            )

            logger.info(
                f"Batch deduction successful: {result['successful']}/{result['total']} items, "
                f"cost=${result['total_cost']}"
            )

            return result

        except Exception as e:
            logger.error(f"Batch deduction failed: {e}")
            raise

    async def deduct_stock(
        self,
        item_sku: str,
        quantity: Decimal,
        user_id: str,
        username: str = "system",
        reference_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Deduct single item from inventory (FIFO).

        Args:
            item_sku: Item SKU to deduct
            quantity: Quantity to deduct
            user_id: User performing operation
            username: Username for audit
            reference_id: Optional reference (tank_id, etc.)
            notes: Optional notes

        Returns:
            Dict with deduction details and cost
        """
        try:
            # Get item by SKU
            from app.database import fetch_one
            item = await fetch_one(
                "SELECT id FROM item_master WHERE sku = $1 AND is_active = TRUE",
                item_sku
            )

            if not item:
                raise ValueError(f"Item with SKU '{item_sku}' not found")

            # Create use stock request
            request = UseStockRequest(
                item_master_id=item["id"],
                quantity=quantity,
                purpose=f"{self.module_name} operation",
                module_reference=self.module_ref.value,
                tank_id=reference_id,
                notes=notes
            )

            # Execute deduction
            result = await inventory_service.use_stock_fifo(
                request=request,
                user_id=user_id,
                username=username
            )

            return result

        except Exception as e:
            logger.error(f"Stock deduction failed for {item_sku}: {e}")
            raise

    # ========================================================================
    # STOCK INFORMATION
    # ========================================================================

    async def bulk_fetch(
        self,
        skus: Optional[List[str]] = None,
        item_ids: Optional[List[int]] = None,
        include_reserved: bool = True,
        include_batches: bool = False
    ) -> Dict:
        """
        Fetch multiple items efficiently.

        Args:
            skus: List of SKUs to fetch
            item_ids: List of item IDs to fetch
            include_reserved: Include reserved quantities
            include_batches: Include batch details

        Returns:
            Dict with keys:
                - items: List[dict]
                - total: int
                - found: int
                - not_found: List[str/int]

        Example:
            items = await inv.bulk_fetch(
                skus=["FEED-PELLET-3MM", "CHEM-PH-DOWN"],
                include_reserved=True
            )
            for item in items["items"]:
                print(f"{item['name']}: {item['available_qty']} {item['unit']}")
        """
        try:
            request = BulkFetchRequest(
                skus=skus,
                item_ids=item_ids,
                include_reserved=include_reserved,
                include_batches=include_batches
            )

            result = await inventory_service.bulk_fetch_items(request)
            return result

        except Exception as e:
            logger.error(f"Bulk fetch failed: {e}")
            raise

    async def get_item_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Get single item by SKU.

        Args:
            sku: Item SKU

        Returns:
            Item dict or None if not found
        """
        result = await self.bulk_fetch(skus=[sku])
        if result["items"]:
            return result["items"][0]
        return None

    async def check_availability(self, sku: str) -> Dict:
        """
        Check if item is available and get current quantity.

        Args:
            sku: Item SKU

        Returns:
            Dict with:
                - available: bool
                - current_qty: Decimal
                - reserved_qty: Decimal
                - available_qty: Decimal
                - unit: str
        """
        item = await self.get_item_by_sku(sku)

        if not item:
            return {
                "available": False,
                "current_qty": Decimal("0"),
                "reserved_qty": Decimal("0"),
                "available_qty": Decimal("0"),
                "unit": None
            }

        return {
            "available": item.get("current_qty", 0) > 0,
            "current_qty": item.get("current_qty", 0),
            "reserved_qty": item.get("reserved_qty", 0),
            "available_qty": item.get("available_qty", 0),
            "unit": item.get("unit")
        }

    # ========================================================================
    # RESERVATIONS
    # ========================================================================

    async def create_reservation(
        self,
        item_sku: str,
        quantity: Decimal,
        module_reference: str,
        reference_id: Optional[str] = None,
        duration_hours: int = 24,
        notes: Optional[str] = None,
        user_id: str = None
    ) -> Dict:
        """
        Reserve stock for planned operation (soft lock).

        Args:
            item_sku: Item SKU to reserve
            quantity: Quantity to reserve
            module_reference: Module name
            reference_id: Optional reference (tank_id, etc.)
            duration_hours: Reservation duration (default: 24h)
            notes: Optional notes
            user_id: User creating reservation

        Returns:
            Reservation details dict

        Example:
            reservation = await inv.create_reservation(
                item_sku="FEED-PELLET-3MM",
                quantity=Decimal("10.0"),
                module_reference="biofloc",
                reference_id=str(tank_id),
                duration_hours=24,
                notes="Reserved for tomorrow's feeding"
            )
        """
        try:
            # Get item by SKU
            from app.database import fetch_one
            item = await fetch_one(
                "SELECT id FROM item_master WHERE sku = $1 AND is_active = TRUE",
                item_sku
            )

            if not item:
                raise ValueError(f"Item with SKU '{item_sku}' not found")

            # Create reservation request
            request = CreateReservationRequest(
                item_id=item["id"],
                quantity=quantity,
                module_reference=ModuleType(module_reference.lower()),
                reference_id=reference_id,
                duration_hours=duration_hours,
                notes=notes
            )

            # Create reservation
            result = await inventory_service.create_reservation(
                request=request,
                user_id=user_id
            )

            logger.info(f"Created reservation for {quantity} {item_sku}")
            return result

        except Exception as e:
            logger.error(f"Reservation creation failed: {e}")
            raise

    async def cancel_reservation(self, reservation_id: str) -> Dict:
        """
        Cancel a pending reservation.

        Args:
            reservation_id: Reservation UUID

        Returns:
            Success dict
        """
        return await inventory_service.cancel_reservation(reservation_id)

    async def confirm_reservation(
        self,
        reservation_id: str,
        user_id: str,
        username: str = "system"
    ) -> Dict:
        """
        Convert reservation to actual stock usage.

        Args:
            reservation_id: Reservation UUID
            user_id: User confirming
            username: Username for audit

        Returns:
            Dict with deduction details
        """
        return await inventory_service.confirm_reservation(
            reservation_id=reservation_id,
            user_id=user_id,
            username=username
        )

    # ========================================================================
    # REPORTING
    # ========================================================================

    async def get_consumption_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days_back: int = 30
    ) -> Dict:
        """
        Get consumption report for this module.

        Args:
            start_date: Report start date
            end_date: Report end date
            days_back: Days to look back if dates not provided

        Returns:
            Dict with:
                - module_name: str
                - items: List[dict] (consumed items)
                - total_cost: Decimal
                - total_items: int
                - period_days: int
        """
        return await inventory_service.get_module_consumption(
            module_name=self.module_name,
            days_back=days_back
        )

    async def get_module_items(self) -> Dict:
        """
        Get all items mapped to this module.

        Returns:
            Dict with items list
        """
        return await inventory_service.get_module_items(
            module_name=self.module_name
        )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def get_low_stock_items(self) -> List[Dict]:
        """
        Get items used by this module that are low on stock.

        Returns:
            List of items below reorder threshold
        """
        from app.database import fetch_all

        items = await fetch_all(
            """
            SELECT
                im.id,
                im.item_name,
                im.sku,
                im.category,
                im.unit,
                im.current_qty,
                im.reorder_threshold,
                (im.reorder_threshold - im.current_qty) as deficit
            FROM item_master im
            INNER JOIN item_module_mapping imm ON im.id = imm.item_id
            WHERE imm.module_name = $1
              AND im.is_active = TRUE
              AND im.current_qty <= im.reorder_threshold
            ORDER BY deficit DESC
            """,
            self.module_name
        )

        return items

    async def estimate_days_remaining(self, sku: str, daily_usage: Decimal) -> Optional[float]:
        """
        Estimate how many days of stock remain based on daily usage.

        Args:
            sku: Item SKU
            daily_usage: Average daily usage quantity

        Returns:
            Days remaining (float) or None if item not found
        """
        availability = await self.check_availability(sku)

        if not availability["available"] or daily_usage <= 0:
            return None

        days = float(availability["available_qty"] / daily_usage)
        return days
