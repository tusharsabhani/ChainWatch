from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from app.config import Settings

_UNSAFE_SEGMENT_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def _sanitize_segment(value: str, fallback: str) -> str:
    sanitized = _UNSAFE_SEGMENT_PATTERN.sub("-", value).strip(".-")
    return sanitized or fallback


class StorageManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def managed_directories(self) -> tuple[Path, ...]:
        return (
            self.settings.data_dir,
            self.settings.imports_raw_dir,
            self.settings.imports_processed_dir,
            self.settings.reports_json_dir,
            self.settings.reports_markdown_dir,
            self.settings.cache_external_risk_dir,
            self.settings.logs_app_dir,
            self.settings.logs_agent_runs_dir,
        )

    def ensure_runtime_paths(self) -> None:
        for directory in self.managed_directories:
            directory.mkdir(parents=True, exist_ok=True)
        self.settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_within_data_root(self, candidate: Path) -> Path:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.settings.data_dir)
        except ValueError as exc:
            raise ValueError("Path must remain within the managed data directory.") from exc
        return resolved

    def resolve_in_data(self, relative_path: str | Path) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute():
            candidate = relative
        else:
            candidate = self.settings.data_dir / relative
        return self._ensure_within_data_root(candidate)

    def report_json_path(self, report_id: str) -> Path:
        safe_report_id = _sanitize_segment(report_id, "report")
        return self._ensure_within_data_root(
            self.settings.reports_json_dir / f"{safe_report_id}.json"
        )

    def report_markdown_path(self, report_id: str) -> Path:
        safe_report_id = _sanitize_segment(report_id, "report")
        return self._ensure_within_data_root(
            self.settings.reports_markdown_dir / f"{safe_report_id}.md"
        )

    def external_risk_cache_path(self, cache_key: str) -> Path:
        digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
        return self._ensure_within_data_root(
            self.settings.cache_external_risk_dir / f"{digest}.json"
        )

    def import_raw_path(self, import_id: str, filename: str) -> Path:
        safe_import_id = _sanitize_segment(import_id, "import")
        safe_filename = _sanitize_segment(filename, "upload.csv")
        return self._ensure_within_data_root(
            self.settings.imports_raw_dir / f"{safe_import_id}-{safe_filename}"
        )

    def import_processed_summary_path(self, import_id: str) -> Path:
        safe_import_id = _sanitize_segment(import_id, "import")
        return self._ensure_within_data_root(
            self.settings.imports_processed_dir / f"{safe_import_id}.json"
        )

    def app_log_path(self, log_date: date | None = None) -> Path:
        safe_date = (log_date or date.today()).isoformat()
        return self._ensure_within_data_root(
            self.settings.logs_app_dir / f"app-{safe_date}.log"
        )

    def agent_run_log_path(self, run_id: str) -> Path:
        safe_run_id = _sanitize_segment(run_id, "agent-run")
        return self._ensure_within_data_root(
            self.settings.logs_agent_runs_dir / f"{safe_run_id}.log"
        )

    def persist_raw_import(self, source_path: Path, import_id: str, filename: str | None = None) -> Path:
        resolved_source = source_path.resolve()
        if not resolved_source.exists():
            raise FileNotFoundError(f"Import source does not exist: {resolved_source}")

        destination = self.import_raw_path(import_id, filename or resolved_source.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolved_source, destination)
        return destination

    def write_json_artifact(self, destination: Path, payload: Any) -> Path:
        path = self._ensure_within_data_root(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def write_markdown_artifact(self, destination: Path, content: str) -> Path:
        path = self._ensure_within_data_root(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_external_risk_cache(self, cache_key: str, payload: Any) -> Path:
        return self.write_json_artifact(self.external_risk_cache_path(cache_key), payload)

    def write_import_processed_summary(self, import_id: str, payload: Any) -> Path:
        return self.write_json_artifact(self.import_processed_summary_path(import_id), payload)

    def read_external_risk_cache(self, cache_key: str) -> Any | None:
        path = self.external_risk_cache_path(cache_key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
