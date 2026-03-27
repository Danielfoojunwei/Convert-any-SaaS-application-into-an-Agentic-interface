---
name: "list_products"
description: "List all products in the bakery catalog"
version: 0.1.0
idempotent: true
domain: products
execution_backend: api
---

# list_products

List all products in the bakery catalog

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | `string` | No | Filter by product category |
| `limit` | `integer` | No | Number of results per page |
| `page` | `integer` | No | Page number for pagination |
| `query` | `string` | No | Search query for products |
| `min_price` | `number` | No | Minimum price filter |
| `max_price` | `number` | No | Maximum price filter |

**`category` values**: `cakes`, `pastries`, `bread`, `custom`

## Output

Returns an array of objects with the following fields:

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
| `image_url` | `string` | Product image URL |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "list_products",
  "arguments": {
  "category": "cakes",
  "limit": 1,
  "page": 1,
  "query": "example_query",
  "min_price": 1.0,
  "max_price": 1.0
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
