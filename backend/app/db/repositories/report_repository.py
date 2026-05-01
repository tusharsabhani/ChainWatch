from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from app.db.repositories.base import SQLiteRepository
from app.schemas.reports import (
    ReportRecord,
    ReportRequest,
    ReportStatus,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReportRepository(SQLiteRepository):
    def create_report(
        self,
        *,
        report_id: str,
        request: ReportRequest,
        title: str,
    ) -> ReportRecord:
        created_at = _utc_now_iso()
        self.execute(
            """
            INSERT INTO reports (
                id,
                report_type,
                scope_type,
                scope_id,
                title,
                status,
                requested_by,
                created_at,
                completed_at,
                json_path,
                markdown_path,
                summary,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL)
            """,
            (
                report_id,
                request.report_type.value,
                request.scope_type.value,
                request.scope_id,
                title,
                ReportStatus.QUEUED.value,
                request.requested_by,
                created_at,
            ),
        )
        report = self.get_report(report_id)
        if report is None:
            raise RuntimeError(f"Report creation failed for {report_id}")
        return report

    def mark_running(self, report_id: str) -> ReportRecord:
        self.execute(
            """
            UPDATE reports
            SET status = ?,
                error_message = NULL
            WHERE id = ?
            """,
            (
                ReportStatus.RUNNING.value,
                report_id,
            ),
        )
        report = self.get_report(report_id)
        if report is None:
            raise RuntimeError(f"Report {report_id} was not found after starting.")
        return report

    def finalize_report(
        self,
        *,
        report_id: str,
        status: ReportStatus,
        json_path: str | None,
        markdown_path: str | None,
        summary: str | None,
        error_message: str | None,
    ) -> ReportRecord:
        completed_at = _utc_now_iso()
        self.execute(
            """
            UPDATE reports
            SET status = ?,
                completed_at = ?,
                json_path = ?,
                markdown_path = ?,
                summary = ?,
                error_message = ?
            WHERE id = ?
            """,
            (
                status.value,
                completed_at,
                json_path,
                markdown_path,
                summary,
                error_message,
                report_id,
            ),
        )
        report = self.get_report(report_id)
        if report is None:
            raise RuntimeError(f"Report {report_id} was not found after finalizing.")
        return report

    def get_report(self, report_id: str) -> ReportRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                report_type,
                scope_type,
                scope_id,
                title,
                status,
                requested_by,
                created_at,
                completed_at,
                json_path,
                markdown_path,
                summary,
                error_message
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        )
        if row is None:
            return None
        return ReportRecord.model_validate(dict(row))

    def list_reports(
        self,
        *,
        scope_type: str | None = None,
        status: ReportStatus | None = None,
        limit: int = 20,
    ) -> list[ReportRecord]:
        conditions: list[str] = []
        params: list[object] = []
        if scope_type:
            conditions.append("scope_type = ?")
            params.append(scope_type)
        if status is not None:
            conditions.append("status = ?")
            params.append(status.value)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self.fetch_all(
            f"""
            SELECT
                id,
                report_type,
                scope_type,
                scope_id,
                title,
                status,
                requested_by,
                created_at,
                completed_at,
                json_path,
                markdown_path,
                summary,
                error_message
            FROM reports
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [*params, limit],
        )
        return [ReportRecord.model_validate(dict(row)) for row in rows]
