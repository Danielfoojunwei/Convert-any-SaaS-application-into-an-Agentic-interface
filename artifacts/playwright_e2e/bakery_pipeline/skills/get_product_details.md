---
name: "get_product_details"
description: "Get full details for a specific product"
version: 0.1.0
idempotent: true
domain: products
execution_backend: api
---

# get_product_details

Get full details for a specific product

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `productId` | `string` | Yes | Product identifier |
| `product_id` | `string` | Yes | Product identifier |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` |  |
| `name` | `string` |  |
| `description` | `string` |  |
| `price` | `number` |  |
| `currency` | `string` |  |
| `category` | `string` |  |
| `in_stock` | `boolean` |  |
| `images` | `array` |  |
| `variants` | `array` | Product variants (size, color, etc.) |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "get_product_details",
  "arguments": {
  "productId": "example_productId",
  "product_id": "example_product_id"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
