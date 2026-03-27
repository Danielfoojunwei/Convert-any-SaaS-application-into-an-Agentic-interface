---
name: "apply_coupon"
description: "Apply a coupon or discount code to the cart"
version: 0.1.0
idempotent: true
domain: cart
execution_backend: hybrid
---

# apply_coupon

Apply a coupon or discount code to the cart

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | `string` | Yes | Coupon or discount code |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `applied` | `boolean` | Whether the code was accepted |
| `discount_amount` | `number` | Discount amount |
| `new_subtotal` | `number` | Cart subtotal after discount |
| `message` | `string` | Coupon status message |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "apply_coupon",
  "arguments": {
  "code": "example_code"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
