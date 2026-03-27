---
name: "initiate_return"
description: "Start a return or refund request for an order"
version: 0.1.0
idempotent: false
domain: orders
execution_backend: hybrid
---

# initiate_return

Start a return or refund request for an order

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_id` | `string` | Yes | Order identifier |
| `item_ids` | `array` | Yes | List of item IDs to return |
| `reason` | `string` | Yes | Reason for return |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `return_id` | `string` | Return request ID |
| `status` | `string` | Return request status |
| `return_label_url` | `string` | Return shipping label URL |
| `refund_amount` | `number` | Expected refund amount |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "initiate_return",
  "arguments": {
  "order_id": "example_order_id",
  "reason": "example_reason"
}
}
```

## Retry Safety

This tool is **NOT idempotent** — do not retry without checking state first.
