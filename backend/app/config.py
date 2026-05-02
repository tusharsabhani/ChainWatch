from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_backend_env_file() -> Path:
    return Path(__file__).resolve().parents[1] / ".env"


def _resolve_repo_path(repo_root: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_default_backend_env_file()),
        env_prefix="CHAINWATCH_",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "ChainWatch Backend"
    app_version: str = "0.1.0"
    environment: str = "development"

    repo_root: Path = Field(default_factory=_default_repo_root)
    data_dir: Path = Path("data")
    database_path: Path = Path("data/app.db")
    imports_raw_dir: Path = Path("data/imports/raw")
    imports_processed_dir: Path = Path("data/imports/processed")
    reports_json_dir: Path = Path("data/reports/json")
    reports_markdown_dir: Path = Path("data/reports/markdown")
    cache_external_risk_dir: Path = Path("data/cache/external_risk")
    logs_app_dir: Path = Path("data/logs/app")
    logs_agent_runs_dir: Path = Path("data/logs/agent_runs")

    llm_provider: str | None = None
    llm_api_key: str | None = None
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "CHAINWATCH_OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-5.2",
        validation_alias=AliasChoices("OPENAI_MODEL", "CHAINWATCH_OPENAI_MODEL"),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_BASE_URL", "CHAINWATCH_OPENAI_BASE_URL"),
    )
    search_provider: str | None = None
    search_api_key: str | None = None
    exa_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EXA_API_KEY", "CHAINWATCH_EXA_API_KEY"),
    )

    reports_enabled: bool = True
    external_risk_refresh_enabled: bool = True
    external_risk_cache_ttl_hours: int = 24
    external_risk_cache_same_day_only: bool = True

    sqlite_timeout_seconds: float = 5.0

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        self.repo_root = self.repo_root.resolve()

        path_fields = (
            "data_dir",
            "database_path",
            "imports_raw_dir",
            "imports_processed_dir",
            "reports_json_dir",
            "reports_markdown_dir",
            "cache_external_risk_dir",
            "logs_app_dir",
            "logs_agent_runs_dir",
        )

        for field_name in path_fields:
            resolved = _resolve_repo_path(self.repo_root, getattr(self, field_name))
            setattr(self, field_name, resolved)

        return self

    @property
    def llm_configured(self) -> bool:
        return bool(self.resolved_llm_provider and self.resolved_llm_api_key)

    @property
    def resolved_llm_provider(self) -> str | None:
        if self.llm_provider:
            normalized = self.llm_provider.strip().lower()
            return normalized or None
        if self.openai_api_key or self.llm_api_key:
            return "openai"
        return None

    @property
    def resolved_llm_api_key(self) -> str | None:
        provider = self.resolved_llm_provider
        if provider == "openai":
            return self.openai_api_key or self.llm_api_key
        return self.llm_api_key

    @property
    def resolved_search_provider(self) -> str | None:
        if self.search_provider:
            normalized = self.search_provider.strip().lower()
            return normalized or None
        if self.exa_api_key or self.search_api_key:
            return "exa"
        return None

    @property
    def resolved_search_api_key(self) -> str | None:
        provider = self.resolved_search_provider
        if provider == "exa":
            return self.exa_api_key or self.search_api_key
        return self.search_api_key

    @property
    def search_configured(self) -> bool:
        return bool(self.resolved_search_provider and self.resolved_search_api_key)

    def to_relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            return str(path.resolve())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
