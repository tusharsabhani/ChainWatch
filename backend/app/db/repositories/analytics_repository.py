from __future__ import annotations

from collections.abc import Sequence

from app.db.repositories.base import SQLiteRepository


def _placeholders(items: Sequence[object]) -> str:
    return ", ".join("?" for _ in items)


class AnalyticsRepository(SQLiteRepository):
    def list_sales_history_rows(
        self,
        *,
        product_ids: list[int],
        region_filter: str | None = None,
        channel_filter: str | None = None,
    ) -> list[dict[str, object]]:
        if not product_ids:
            return []

        params: list[object] = list(product_ids)
        conditions = [f"product_id IN ({_placeholders(product_ids)})"]
        if region_filter:
            conditions.append("region_code = ?")
            params.append(region_filter)
        if channel_filter:
            conditions.append("channel = ?")
            params.append(channel_filter)

        rows = self.fetch_all(
            f"""
            SELECT
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
            FROM sales_history
            WHERE {' AND '.join(conditions)}
            ORDER BY sales_date ASC
            """,
            params,
        )
        return [dict(row) for row in rows]

    def list_latest_inventory_snapshots(self, *, product_ids: list[int]) -> list[dict[str, object]]:
        if not product_ids:
            return []
        rows = self.fetch_all(
            f"""
            SELECT inv.*
            FROM inventory_snapshots AS inv
            INNER JOIN (
                SELECT
                    product_id,
                    warehouse_code,
                    MAX(snapshot_date) AS latest_snapshot_date
                FROM inventory_snapshots
                WHERE product_id IN ({_placeholders(product_ids)})
                GROUP BY product_id, warehouse_code
            ) latest
                ON latest.product_id = inv.product_id
               AND latest.warehouse_code = inv.warehouse_code
               AND latest.latest_snapshot_date = inv.snapshot_date
            ORDER BY inv.product_id ASC, inv.warehouse_code ASC
            """,
            product_ids,
        )
        return [dict(row) for row in rows]

    def list_latest_fulfillment_snapshots(
        self,
        *,
        product_ids: list[int] | None = None,
        region_codes: list[str] | None = None,
    ) -> list[dict[str, object]]:
        conditions: list[str] = []
        params: list[object] = []
        if product_ids:
            conditions.append(f"product_id IN ({_placeholders(product_ids)})")
            params.extend(product_ids)
        if region_codes:
            conditions.append(f"region_code IN ({_placeholders(region_codes)})")
            params.extend(region_codes)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self.fetch_all(
            f"""
            SELECT full.*
            FROM fulfillment_snapshots AS full
            INNER JOIN (
                SELECT
                    COALESCE(product_id, -1) AS product_scope,
                    region_code,
                    COALESCE(warehouse_code, '') AS warehouse_scope,
                    MAX(captured_at) AS latest_captured_at
                FROM fulfillment_snapshots
                {where_clause}
                GROUP BY COALESCE(product_id, -1), region_code, COALESCE(warehouse_code, '')
            ) latest
                ON COALESCE(full.product_id, -1) = latest.product_scope
               AND full.region_code = latest.region_code
               AND COALESCE(full.warehouse_code, '') = latest.warehouse_scope
               AND full.captured_at = latest.latest_captured_at
            ORDER BY full.region_code ASC, full.warehouse_code ASC
            """,
            params,
        )
        return [dict(row) for row in rows]
