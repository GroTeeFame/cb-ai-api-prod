# Chatbot AI API (Current State)

## Base URL and Routes

Base URL: **TBD (not hosted yet)**.

When deployed, should use:

- `http://<host>:<port>` (or your final domain)

Application routes:

- `POST /v1/chatbot/turn`
- `GET /health/ready`
- `GET /health/live`

## Common Behavior

- Content type: `application/json`
- Request ID header:
  - `X-Request-ID`
  - Response always includes the same header value (or generated UUID if missing)
- Default language is Ukrainian (`uk`) if not provided.

## Endpoint: `POST /v1/chatbot/turn`

Primary endpoint used by chatbot backend to send user turns.

`chat_id` must be stable for the same conversation across all turns.

### Request Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `chat_id` | `string` | Yes | Conversation identifier. Keep constant for one dialog. |
| `user_id` | `string \| null` | No | End-user identifier if available. |
| `message_id` | `string \| null` | No | Upstream message identifier if available. |
| `text` | `string` | Yes | User message text. |
| `is_private` | `boolean` | No | Defaults to `true` if omitted. |
| `context` | `object` | No | Defaults to empty object if omitted. |
| `context.language` | `string \| null` | No | Defaults to `uk` if omitted. |
| `context.timezone` | `string \| null` | No | Example: `Europe/Kyiv`. |
| `context.slots` | `object` | No | Optional contextual slots, e.g. `client_id`. |
| `metadata` | `object` | No | Optional transport/channel metadata. |

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
- If `event == "function"` with unknown `data`, log it and fall back to safe user message/standard support flow.


### Prompt-Driven Behavior (Current State)

Scope and escalation are currently driven by LLM prompt instructions (not strict deterministic router code). Backend must always handle both:

- normal text replies (`event="send"`)
- operator handoff signal (`event="function"`, `data="connect_with_operator()"`)

## Health Endpoints

- `GET /health/ready` -> `{"status":"ok"}`
- `GET /health/live` -> `{"status":"alive"}`

## Error and Validation Behavior

- Invalid request body shape/types -> HTTP `422` (FastAPI validation).
- Runtime failures in orchestration are generally converted to fallback `200` response:
  - `event="send"`
  - user-facing apology text in selected language.
