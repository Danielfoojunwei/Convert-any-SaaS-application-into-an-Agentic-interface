---
name: "get_business_info"
description: "Get business contact information, hours, and location"
version: 0.1.0
idempotent: true
domain: info
execution_backend: browser
---

# get_business_info

Get business contact information, hours, and location

## Parameters

No parameters required.

## Output

Returns a confirmation message.

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "get_business_info",
  "arguments": {}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
