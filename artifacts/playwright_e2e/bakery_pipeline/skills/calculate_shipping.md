---
name: "calculate_shipping"
description: "Calculate shipping options and costs for delivery address"
version: 0.1.0
idempotent: true
domain: checkout
execution_backend: hybrid
---

# calculate_shipping

Calculate shipping options and costs for delivery address

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `zip_code` | `string` | Yes | Delivery ZIP/postal code |
| `country` | `string` | No | Delivery country code (ISO 3166-1 alpha-2) |

## Output

Returns an object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `options` | `array` | Available shipping options |
| `cheapest_option` | `object` | Lowest cost option |
| `fastest_option` | `object` | Fastest delivery option |

## Errors

| Error | Recovery | Retryable |
|-------|----------|-----------|
| `NOT_FOUND` | fix_params | No |
| `INVALID_PARAM` | fix_params | No |
| `SERVER_ERROR` | retry | Yes |

## Example

```json
{
  "tool": "calculate_shipping",
  "arguments": {
  "zip_code": "example_zip_code"
}
}
```

## Retry Safety

This tool is **idempotent** — safe to retry on failure.
