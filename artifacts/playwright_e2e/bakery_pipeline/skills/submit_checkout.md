---
name: "submit_checkout"
description: "Initiate checkout - returns payment URL for confirmation"
version: 0.1.0
idempotent: false
domain: checkout
execution_backend: api
---

# submit_checkout

Initiate checkout - returns payment URL for confirmation

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `shipping_address` | `object` | Yes | Delivery address |
| `email` | `string` | Yes | Customer email for confirmation |
| `shipping_method` | `string` | No | Selected shipping method |
| `full_name` | `string` | Yes | Full Name |
| `address` | `string` | Yes | Shipping Address |
| `zip_code` | `string` | Yes | ZIP Code |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `checkout_id` | `string` |  |
| `payment_url` | `string` |  |
| `total` | `number` |  |
| `currency` | `string` |  |
| `expires_at` | `string` | When this checkout session expires |

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
  "tool": "submit_checkout",
  "arguments": {
  "email": "example_email",
  "full_name": "example_full_name",
  "address": "example_address",
  "zip_code": "example_zip_code"
}
}
```

## Retry Safety

This tool is **NOT idempotent** — do not retry without checking state first.
