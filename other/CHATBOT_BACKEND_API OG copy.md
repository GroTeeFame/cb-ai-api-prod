# Chatbot Backend Integration API (Current State)

Last updated: 2026-03-09

This document describes the current HTTP contract exposed by `apichatbot-prod` for chatbot-backend integration.

## Base URL and Routes

Application routes:

- `POST /v1/chatbot/turn`
- `POST /v1/chatbot/direct-answer`
- `GET /health/ready`
- `GET /health/live`

In deployment examples, service runs on port `20001`.

## Common Behavior

- Content type: `application/json`
- Request ID header:
  - Optional inbound header: `X-Request-ID` (configurable via `REQUEST_ID_HEADER`)
  - Response always includes the same header value (or generated UUID if missing)
- Default language is Ukrainian (`uk`) if not provided.
- Conversation memory is in-memory per `chat_id` with TTL 2 hours.
- Internal `context_updates` are not included in API responses.

## Endpoint: `POST /v1/chatbot/turn`

Primary endpoint used by chatbot backend to send user turns.

### Request Body

```json
{
  "chat_id": "chat-123",
  "user_id": "user-456",
  "message_id": "msg-789",
  "text": "Де ваше відділення у Києві?",
  "is_private": true,
  "context": {
    "language": "uk",
    "timezone": "Europe/Kyiv",
    "slots": {
      "client_id": 12345
    }
  },
  "metadata": {
    "channel": "telegram"
  }
}
```

### Response Body

```json
{
  "event": "send",
  "data": "..."
}
```

`event` values currently used:

- `send`: chatbot backend should send `data` to end user as text.
- `function`: chatbot backend should execute function-style integration based on `data`.

### Current `function` Payload (Operator Handoff)

When LLM selects operator escalation tool, response is:

```json
{
  "event": "function",
  "data": "connect_with_operator()"
}
```

Backend action required:

- Treat `data == "connect_with_operator()"` as handoff to human operator.
- Start backend-side operator escalation flow.

Notes:

- `client_id` for escalation is optional at tool schema level.
- Server currently resolves `client_id` from inbound context (`slots`/`metadata`) internally, but it is not embedded into returned `data`.

### Known Prompt-Driven Behavior (Current State)

Scope and escalation are currently driven by LLM prompt instructions (not strict deterministic router code). Backend must always handle both:

- normal text replies (`event="send"`)
- operator handoff signal (`event="function"`, `data="connect_with_operator()"`)

## Endpoint: `POST /v1/chatbot/direct-answer`

Convenience endpoint for plain question-answer usage.

### Request Body

```json
{
  "question": "Які у банку години роботи?",
  "language": "uk"
}
```

### Response Body

```json
{
  "event": "send",
  "data": "..."
}
```

Notes:

- This endpoint currently does not pass tools to LLM, so expected response is text (`event="send"`).

## Health Endpoints

- `GET /health/ready` -> `{"status":"ok"}`
- `GET /health/live` -> `{"status":"alive"}`

## Tooling Exposed to LLM (Internal)

Current registered tools:

- `get_bank_info`
  - topic enum currently: `bank_branches`
- `connect_with_operator`
  - optional argument: `client_id` (integer)

These tools are internal LLM tools; chatbot backend integration point remains only the HTTP response (`event`, `data`).

## Error and Validation Behavior

- Invalid request body shape/types -> HTTP `422` (FastAPI validation).
- Runtime failures in orchestration are generally converted to fallback `200` response:
  - `event="send"`
  - user-facing apology text in selected language.

## Integration Checklist for Chatbot Backend

1. Send each user turn to `POST /v1/chatbot/turn`.
2. Include stable `chat_id` for conversation continuity.
3. Keep passing known context in `context.slots` (for example `client_id`).
4. On response:
   - if `event="send"`: display `data` to user.
   - if `event="function"` and `data="connect_with_operator()"`: trigger operator handoff workflow.
5. Preserve and pass `X-Request-ID` for traceability.
