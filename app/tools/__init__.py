from __future__ import annotations

import inspect
import json
from typing import Any, Dict, Iterable, List

from app.schemas.state import ConversationState

from .operator import OPERATOR_TOOLS, connect_with_operator

# from .balance import BALANCE_TOOLS, lookup_client_balances, lookup_total_balance
from .info import INFO_TOOLS, get_bank_info
from .types import ToolExecutionResult

class UnknownToolError(Exception):
    """Raised when an LLM requests an unknown tool."""


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "get_bank_info": {
        "schema": INFO_TOOLS[0],
        "executor": get_bank_info
    },
    "connect_with_operator": {
        "schema": OPERATOR_TOOLS[0],
        "executor": connect_with_operator
    },

}


def tool_schemas() -> List[Dict[str, Any]]:
    """Return the list of tool specifications exposed to the LLM."""
    return [entry["schema"] for entry in TOOL_REGISTRY.values()]


def execute_tool(
    *,
    name: str,
    arguments: str,
    state: ConversationState,
    language: str,
) -> ToolExecutionResult:
    """
    Execute a tool requested by the LLM.

    Parameters
    ----------
    name:
        Tool identifier supplied by the LLM.
    arguments:
        JSON string containing tool parameters.
    state:
        Current conversation state snapshot.
    language:
        Preferred reply language.
    """
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        raise UnknownToolError(f"Tool '{name}' is not registered.")

    try:
        parsed_args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid arguments for tool '{name}': {arguments}") from exc

    executor = entry["executor"]
    sig = inspect.signature(executor)
    kwargs: Dict[str, Any] = {}
    for name in sig.parameters.keys():
        if name == "state":
            kwargs[name] = state
        elif name == "language":
            kwargs[name] = language
        else:
            kwargs[name] = parsed_args.get(name)

    result = executor(**kwargs)
    if isinstance(result, ToolExecutionResult):
        event = result.event or "send"
        if result.post_process and not isinstance(result.data, str):
            try:
                data = json.dumps(result.data, ensure_ascii=False)
            except TypeError:
                data = str(result.data)
        else:
            data = "" if result.data is None else str(result.data)
        updates = result.context_updates or {}
        return ToolExecutionResult(
            event=event,
            data=data,
            context_updates=updates,
            post_process=result.post_process,
        )

    # Backward compatibility: allow old-style tuple responses.
    if isinstance(result, tuple) and len(result) == 2:
        reply_text, updates = result
        return ToolExecutionResult(
            event="send",
            data=str(reply_text or ""),
            context_updates=updates or {},
            post_process=False,
        )

    raise TypeError(
        f"Tool '{name}' returned unsupported result type: {type(result)!r}"
    )


def merge_context_updates(
    updates_list: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    """Flatten multiple context update dictionaries into a single payload."""
    merged: Dict[str, Any] = {}
    for updates in updates_list:
        if not updates:
            continue
        for key, value in updates.items():
            if key == "slots" and isinstance(value, dict):
                merged.setdefault("slots", {})
                merged["slots"].update(value)
            elif key == "metadata" and isinstance(value, dict):
                merged.setdefault("metadata", {})
                merged["metadata"].update(value)
            else:
                merged[key] = value
    return merged
