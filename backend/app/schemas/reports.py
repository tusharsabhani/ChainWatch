from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.agents import AgentRunStatus, Citation


class ReportStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ReportType(StrEnum):
    RISK_SUMMARY = "risk_summary"
    PRODUCT_RISK = "product_risk"
    COUNTRY_RISK = "country_risk"
    SUPPLIER_RISK = "supplier_risk"
    CHAT_EXPORT = "chat_export"


class ReportScopeType(StrEnum):
    DASHBOARD = "dashboard"
    PRODUCT = "product"
    COUNTRY = "country"
    SUPPLIER = "supplier"
    CHAT = "chat"


class ReportRequest(BaseModel):
    report_type: ReportType
    scope_type: ReportScopeType
    scope_id: str | None = None
    title: str | None = None
    requested_by: str | None = None
    freshness_policy_hours: int = 6


class ReportingAgentInput(ReportRequest):
    report_id: str
    title: str


class ReportArtifactPaths(BaseModel):
    json_path: str | None = None
    markdown_path: str | None = None


class ReportSection(BaseModel):
    section_id: str
    title: str
    status: AgentRunStatus
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class GeneratedReportArtifact(BaseModel):
    report_id: str
    report_type: ReportType
    scope_type: ReportScopeType
    scope_id: str | None = None
    title: str
    generated_at: str
    status: ReportStatus
    summary: str
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    used_agents: list[str] = Field(default_factory=list)
    sections: list[ReportSection] = Field(default_factory=list)
    artifact_paths: ReportArtifactPaths = Field(default_factory=ReportArtifactPaths)


class ReportingAgentOutput(BaseModel):
    report_json: dict[str, Any]
    report_markdown: str | None = None
    summary: str
    artifact_paths: ReportArtifactPaths
    generation_status: ReportStatus
    limitations: list[str] = Field(default_factory=list)


class ReportRecord(BaseModel):
    id: str
    report_type: ReportType
    scope_type: ReportScopeType
    scope_id: str | None = None
    title: str
    status: ReportStatus
    requested_by: str | None = None
    created_at: str
    completed_at: str | None = None
    json_path: str | None = None
    markdown_path: str | None = None
    summary: str | None = None
    error_message: str | None = None


class ReportGenerationResult(BaseModel):
    report: ReportRecord
    output: ReportingAgentOutput
