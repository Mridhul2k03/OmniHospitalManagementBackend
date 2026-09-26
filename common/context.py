"""
Thread-safe ContextVar storage for tenant and request correlation context.
Corresponds to Recipe A of the Multi-Tenant SaaS Blueprint.
"""
import contextvars
from typing import Optional, Any

_current_tenant: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "current_tenant", default=None
)
_current_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_request_id", default=None
)


def set_current_tenant(tenant: Any) -> None:
    _current_tenant.set(tenant)


def get_current_tenant() -> Optional[Any]:
    return _current_tenant.get()


def clear_current_tenant() -> None:
    _current_tenant.set(None)


def set_current_request_id(request_id: str) -> None:
    _current_request_id.set(request_id)


def get_current_request_id() -> Optional[str]:
    return _current_request_id.get()
