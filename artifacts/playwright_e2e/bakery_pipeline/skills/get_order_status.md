---
name: "get_order_status"
description: "Get order status and tracking info"
version: 0.1.0
idempotent: true
domain: orders
execution_backend: api
---

# get_order_status

Get order status and tracking info

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderId` | `string` | Yes | Order identifier |
| `order_id` | `string` | Yes | Order identifier |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `order_id` | `string` |  |
| `status` | `string` |  |
| `items` | `array` |  |
| `total` | `number` |  |
| `tracking_number` | `string` |  |
| `tracking_url` | `string` | Tracking URL |
| `estimated_delivery` | `string` | Estimated delivery date |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "get_order_status",
  "arguments": {
  "orderId": "example_orderId",
  "order_id": "example_order_id"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
