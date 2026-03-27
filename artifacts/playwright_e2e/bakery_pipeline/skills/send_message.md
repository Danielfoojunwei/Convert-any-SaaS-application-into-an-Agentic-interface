---
name: "send_message"
description: "Send a message to the business"
version: 0.1.0
idempotent: false
domain: contact
execution_backend: browser
---

# send_message

Send a message to the business

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sender_name` | `string` | Yes | Your Name |
| `sender_email` | `string` | Yes | Your Email |
| `subject` | `string` | Yes | Subject |
| `body` | `string` | Yes | Your Message |

## Output

Returns a confirmation message.

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |
| `PAYMENT_REQUIRED` | human_intervention | No |

## Example

```json
{
  "tool": "send_message",
  "arguments": {
  "sender_name": "example_sender_name",
  "sender_email": "example_sender_email",
  "subject": "example_subject",
  "body": "example_body"
}
}
```

## Retry Safety

This tool is **NOT idempotent** — do not retry without checking state first.
