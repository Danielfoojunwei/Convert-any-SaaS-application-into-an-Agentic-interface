---
name: "get_cart"
description: "Get current shopping cart contents"
version: 0.1.0
idempotent: true
domain: cart
execution_backend: api
---

# get_cart

Get current shopping cart contents

## Parameters

No parameters required.

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `cart_id` | `string` |  |
| `items` | `array` |  |
| `item_count` | `integer` |  |
| `subtotal` | `number` |  |
| `currency` | `string` |  |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "get_cart",
  "arguments": {}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
