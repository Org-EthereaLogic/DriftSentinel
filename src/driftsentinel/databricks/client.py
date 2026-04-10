"""Build a Databricks WorkspaceClient from unified auth and resolve workspace identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkspaceIdentity:
    """Resolved identity for the current Databricks workspace."""

    host: str
    user: str


def get_workspace_client(**kwargs: Any) -> Any:
    """Return a ``databricks.sdk.WorkspaceClient`` using unified auth.

    All keyword arguments are forwarded to the client constructor.
    Raises ``ImportError`` if ``databricks-sdk`` is not installed.
    """
    try:
        from databricks.sdk import WorkspaceClient  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "databricks-sdk is required for Databricks operations. "
            "Install it with: uv sync --group databricks"
        ) from exc
    return WorkspaceClient(**kwargs)


def resolve_identity(client: Any) -> WorkspaceIdentity:
    """Resolve the current user and workspace host from an authenticated client."""
    me = client.current_user.me()
    return WorkspaceIdentity(
        host=client.config.host,
        user=me.user_name,
    )
