from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from app.schemas.state import ConversationState
from app.tools.types import ToolExecutionResult

logger = logging.getLogger(__name__)

BANK_API_BASE_URL = "http://10.129.132.15:8000"

# CLIENT_SERVICE_BASE_URL = "http://127.0.0.1:8001"


def _resolve_client_id(
    provided_id: Optional[int],
    state: Optional[ConversationState],
) -> Optional[int]:
    if provided_id is not None:
        try:
            return int(provided_id)
        except (TypeError, ValueError):
            return None
    if state:
        for key in ("client_id", "customerid", "customer_id"):
            stored = state.slots.get(key) or state.metadata.get(key)
            if stored is not None:
                try:
                    return int(stored)
                except (TypeError, ValueError):
                    continue
    return None


def connect_with_operator(
    *,
    client_id: Optional[int],
    state: Optional[ConversationState],
    language: Optional[str],
) -> ToolExecutionResult:
    """
    Fetch client accounts to let the LLM choose an account for statements.
    """
    logger.info(f"connect_with_operator() usage inside statement.py")
    logger.info(f"connect_with_operator() tool parameters: client_id={client_id}")
    resolved_id = _resolve_client_id(client_id, state)
    if resolved_id is None:
        logger.warning("connect_with_operator() missing client_id/customerid") #FIXME: 
        resolved_id = 0  # explicit placeholder to avoid 'None'
        # return ToolExecutionResult(
        #     event="send",
        #     data="Потрібен ідентифікатор клієнта, щоб отримати рахунки.",
        #     context_updates={},
        #     post_process=False,
        # ) 

    logger.info(f"connect_with_operator() inside statement.py, resolved_id = {resolved_id}") #TODO:

    call = (
        f"connect_with_operator()" #TODO: 
    )
    logger.info(f"MAKING CALL TO BANK API WITH CALL: call={call}")
    return ToolExecutionResult(
        event="function",
        data=call,
        context_updates={},
        post_process=False,
    )


OPERATOR_TOOLS: list[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "connect_with_operator",
            "description": (
                "Emit a function call to chatbot backend to connect customer with human operator."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "integer",
                        "description": "Identifier of the client in bank database",
                    }
                },
                "additionalProperties": False,
            },
        },
    },
]
# OPERATOR_TOOLS: list[Dict[str, Any]] = [
#     {
#         "type": "function",
#         "function": {
#             "name": "connect_with_operator",
#             "description": (
#                 "Emit a function call to chatbot backend to connect customer with human operator."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "client_id": {
#                         "type": "integer",
#                         "description": "Identifier of the client in bank database",
#                     }
#                 },
#                 "required": ["client_id"],
#                 "additionalProperties": False,
#             },
#         },
#     },
# ]
