from __future__ import annotations

import sqlite3

from app.db.repositories.base import SQLiteRepository


class DataRepository(SQLiteRepository):
    def replace_sales_history_row(
        self,
        *,
        product_id: int,
        sales_date: str,
        channel: str,
        region_code: str,
        units_sold: int,
        gross_revenue: float,
        net_revenue: float,
        returns_qty: int,
        promo_flag: int,
        stockout_flag: int,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.execute(
            """
            DELETE FROM sales_history
            WHERE product_id = ?
              AND sales_date = ?
              AND channel = ?
              AND region_code = ?
            """,
            (product_id, sales_date, channel, region_code),
            connection=connection,
        )
        self.execute(
            """
            INSERT INTO sales_history (
                product_id,
                sales_date,
                channel,
                region_code,
                units_sold,
                gross_revenue,
                net_revenue,
                returns_qty,
                promo_flag,
                stockout_flag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                sales_date,
                channel,
                region_code,
                units_sold,
                gross_revenue,
                net_revenue,
                returns_qty,
                promo_flag,
                stockout_flag,
            ),
            connection=connection,
        )

    def replace_inventory_snapshot_row(
        self,
        *,
        product_id: int,
        warehouse_code: str,
        snapshot_date: str,
        on_hand_qty: int,
        reserved_qty: int,
        inbound_qty: int,
        reorder_point: int,
        safety_stock: int,
        days_of_cover: float | None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.execute(
            """
            DELETE FROM inventory_snapshots
            WHERE product_id = ?
              AND warehouse_code = ?
              AND snapshot_date = ?
            """,
            (product_id, warehouse_code, snapshot_date),
            connection=connection,
        )
        self.execute(
            """
            INSERT INTO inventory_snapshots (
                product_id,
                warehouse_code,
                snapshot_date,
                on_hand_qty,
                reserved_qty,
                inbound_qty,
                reorder_point,
                safety_stock,
                days_of_cover
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                warehouse_code,
                snapshot_date,
                on_hand_qty,
                reserved_qty,
                inbound_qty,
                reorder_point,
                safety_stock,
                days_of_cover,
            ),
            connection=connection,
        )

    def replace_fulfillment_snapshot_row(
        self,
        *,
        product_id: int,
        region_code: str,
        warehouse_code: str | None,
        captured_at: str,
        backlog_orders: int,
        avg_ship_delay_hours: float,
        on_time_rate: float,
        sla_risk_level: int,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.execute(
            """
            DELETE FROM fulfillment_snapshots
            WHERE product_id = ?
              AND region_code = ?
              AND ((warehouse_code IS NULL AND ? IS NULL) OR warehouse_code = ?)
              AND captured_at = ?
            """,
            (
                product_id,
                region_code,
                warehouse_code,
                warehouse_code,
                captured_at,
            ),
            connection=connection,
        )
        self.execute(
            """
            INSERT INTO fulfillment_snapshots (
                product_id,
                region_code,
                warehouse_code,
                captured_at,
                backlog_orders,
                avg_ship_delay_hours,
                on_time_rate,
                sla_risk_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                region_code,
                warehouse_code,
                captured_at,
                backlog_orders,
                avg_ship_delay_hours,
                on_time_rate,
                sla_risk_level,
            ),
            connection=connection,
        )
