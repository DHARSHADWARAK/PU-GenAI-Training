import logging
import os
from contextlib import nullcontext
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def configure_langsmith(settings: Any) -> None:
    if settings.langsmith_api_key:
        os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    if settings.langsmith_endpoint:
        os.environ.setdefault("LANGSMITH_ENDPOINT", settings.langsmith_endpoint)
    if settings.langsmith_project:
        os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)

    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        os.environ.setdefault("LANGCHAIN_CALLBACKS_BACKGROUND", "false")
        logger.info("LangSmith tracing enabled for project '%s'", settings.langsmith_project)
    elif settings.langsmith_tracing:
        logger.warning("LangSmith tracing requested but LANGSMITH_API_KEY is missing")


def traceable(name: str | None = None, run_type: str = "chain") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    try:
        from langsmith import traceable as langsmith_traceable

        return langsmith_traceable(name=name, run_type=run_type)
    except Exception:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            return async_wrapper if getattr(func, "__code__", None) and func.__code__.co_flags & 0x80 else sync_wrapper

        return decorator


def tracing_context(settings: Any, metadata: dict[str, Any] | None = None):
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return nullcontext()
    try:
        import langsmith as ls

        return ls.tracing_context(
            enabled=True,
            project_name=settings.langsmith_project,
            metadata=metadata or {},
        )
    except Exception as exc:
        logger.warning("LangSmith tracing context unavailable: %s", exc)
        return nullcontext()


def flush_traces(settings: Any) -> None:
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers

        wait_for_all_tracers()
    except Exception as exc:
        logger.warning("Unable to flush LangSmith traces: %s", exc)
