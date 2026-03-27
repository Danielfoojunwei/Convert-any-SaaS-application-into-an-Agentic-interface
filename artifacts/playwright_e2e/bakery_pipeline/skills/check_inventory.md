---
name: "check_inventory"
description: "Check real-time stock status for a product variant"
version: 0.1.0
idempotent: true
domain: products
execution_backend: hybrid
---

# check_inventory

Check real-time stock status for a product variant

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | `string` | Yes | Product identifier |
| `variant_id` | `string` | No | Specific variant (size, color) |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | `string` | Product ID |
| `in_stock` | `boolean` | Whether in stock |
| `quantity` | `integer` | Available quantity |
| `restock_date` | `string` | Expected restock date |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "check_inventory",
  "arguments": {
  "product_id": "example_product_id"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
