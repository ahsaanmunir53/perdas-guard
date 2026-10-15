"""Application settings, read from environment variables (and .env in local dev)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Runtime ---
    env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Google Cloud ---
    google_cloud_project: str = ""
    google_cloud_location: str = "global"  # Gemini endpoint location
    gcs_bucket: str = ""  # uploads bucket; empty = keep uploads in memory (dev only)

    # --- AI ---
    # "gemini" uses real Gemini API calls; "fake" uses simulated offline responses.
    gemini_api_key: str = ""
    llm_backend: Literal["gemini", "fake"] = "fake"
    model_fast: str = "gemini-3.8-flash"
    model_pro: str = "gemini-3.1-pro-preview"
    model_tts: str = "gemini-3.8-flash-lite-tts"
    tts_voice: str = "Kore"

    # --- Storage ---
    store_backend: Literal["memory", "firestore"] = "memory"
    graph_backend: Literal["memory", "spanner"] = "memory"
    # The project that holds the Spanner instance. Empty = GOOGLE_CLOUD_PROJECT. Set it when Spanner
    # lives in its own project (for example one with billing for a free trial instance, while the
    # Firebase project stays on the no-cost plan), or to the project id used in the local emulator.
    spanner_project: str = ""
    spanner_instance: str = ""
    spanner_database: str = ""
    # host:port of the local Spanner emulator (127.0.0.1:9010). Empty = real Cloud Spanner. The
    # Spanner client reads this only from the real environment, so it is copied there on start.
    spanner_emulator_host: str = ""

    # --- Security ---
    # dev: X-Dev-User and X-Dev-Role headers, for local work only (the client picks its own role).
    # demo: a public sandbox; every caller is a worker (X-Dev-User may name one), never staff.
    # firebase: Firebase ID tokens, roles from the token's custom claim.
    auth_mode: Literal["dev", "demo", "firebase"] = "dev"
    # Secret used to hash phone/account numbers for the integrity network and to sign evidence locally.
    # In production this comes from Secret Manager, never from code.
    hash_salt: str = "dev-only-salt-change-me"
    evidence_signing_key: str = "dev-only-signing-key-change-me"
    kms_key_version: str = ""  # projects/.../cryptoKeyVersions/1 ; empty = local HMAC signing
    use_sensitive_data_protection: bool = False
    model_armor_template: str = ""  # projects/P/locations/L/templates/T ; empty = local heuristic screen
    scheduler_audience: str = ""  # expected OIDC audience for Cloud Scheduler calls to /api/cases/tick
    scheduler_service_account: str = ""  # expected caller email on the scheduler's OIDC token

    # --- Uploads ---
    max_upload_mb: int = 12
    max_files_per_request: int = 8

    # --- Data ---
    packs_dir: str = ""  # empty = bundled packs
    recruiters_csv: str = ""  # empty = bundled fictional sample

    # --- A2A ---
    partner_agent_card_url: str = ""  # a legal-aid partner's A2A agent card

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    def validate_for_prod(self) -> list[str]:
        """Return a list of configuration problems that must be fixed before serving production traffic."""
        problems: list[str] = []
        if self.auth_mode != "firebase":
            problems.append("AUTH_MODE must be 'firebase' in prod")
        if self.hash_salt.startswith("dev-only") or self.evidence_signing_key.startswith("dev-only"):
            problems.append("HASH_SALT and EVIDENCE_SIGNING_KEY must come from Secret Manager in prod")
        if self.llm_backend != "gemini":
            problems.append("LLM_BACKEND must be 'gemini' in prod")
        if self.store_backend != "firestore":
            problems.append("STORE_BACKEND must be 'firestore' in prod")
        if not self.google_cloud_project:
            problems.append("GOOGLE_CLOUD_PROJECT is required in prod")
        if self.graph_backend == "spanner":
            import os

            if self.spanner_emulator_host or os.environ.get("SPANNER_EMULATOR_HOST"):
                problems.append("SPANNER_EMULATOR_HOST must not be set in prod")
            if not (self.spanner_instance and self.spanner_database):
                problems.append("SPANNER_INSTANCE and SPANNER_DATABASE are required when GRAPH_BACKEND=spanner")
        return problems

    @property
    def spanner_target_project(self) -> str:
        return self.spanner_project or self.google_cloud_project


@lru_cache
def get_settings() -> Settings:
    return Settings()




def export_genai_env(settings: Settings) -> None:
    """Configure Google ADK for Gemini API-key or Google Cloud authentication."""
    import os

    # Offline mode: don't configure Gemini authentication.
    if settings.llm_backend != "gemini":
        return

    # Option 1: Gemini API key (local development / AI Studio).
    if settings.gemini_api_key:
        os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
        os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "false"
        os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
        return

    # Option 2: Google Cloud authentication.
    if settings.google_cloud_project:
        os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project
        os.environ["GOOGLE_CLOUD_LOCATION"] = (
            settings.google_cloud_location
        )
        os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "true"
        os.environ.pop("GOOGLE_API_KEY", None)
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        return

    raise RuntimeError(
        "Gemini mode requires GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT "
        "to be configured."
    )


