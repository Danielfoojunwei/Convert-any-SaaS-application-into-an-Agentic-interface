---
name: "remove_from_cart"
description: "Remove a product from the shopping cart"
version: 0.1.0
idempotent: true
domain: cart
execution_backend: hybrid
---

# remove_from_cart

Remove a product from the shopping cart

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | `string` | Yes | Product identifier to remove |
| `variant_id` | `string` | No | Specific variant to remove |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `cart_id` | `string` | Cart session ID |
| `item_count` | `integer` | Remaining items |
| `subtotal` | `number` | Updated subtotal |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "remove_from_cart",
  "arguments": {
  "product_id": "example_product_id"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
