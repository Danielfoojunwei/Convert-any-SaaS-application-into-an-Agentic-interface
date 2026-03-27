---
name: "search_items"
description: "Search for items on the site"
version: 0.1.0
idempotent: true
domain: search
execution_backend: browser
---

# search_items

Search for items on the site

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `string` | No | Search products... |

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
  "tool": "search_items",
  "arguments": {
  "query": "example_query"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
