---
name: "add_to_cart"
description: "Add a product to the shopping cart"
version: 0.1.0
idempotent: false
domain: cart
execution_backend: api
---

# add_to_cart

Add a product to the shopping cart

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | `string` | Yes | Product identifier |
| `quantity` | `integer` | Yes | Number of items to add |
| `variant_id` | `string` | No | Product variant (size, flavor) |

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
  "tool": "add_to_cart",
  "arguments": {
  "product_id": "example_product_id",
  "quantity": 1
}
}
```

## Retry Safety

This tool is **NOT idempotent** — do not retry without checking state first.
