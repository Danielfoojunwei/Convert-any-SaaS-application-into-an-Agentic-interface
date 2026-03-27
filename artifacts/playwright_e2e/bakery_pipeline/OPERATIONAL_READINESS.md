# Operational Readiness

This document distinguishes **generated interface coverage** from **operational readiness**. It summarizes which tools are route-mapped, which rely on generated browser behavior, and which still require additional hardening before production use.

## Runtime State Model

Starter-grade runtime state model inferred from workflow structure. Useful for generated execution scaffolding, approvals, and session continuity.

| Workflow | Inferred States |
|---|---|
| `purchase_flow` | browsing → cart_review → checkout_ready → payment_pending → order_tracking |

## Session Entities

- `cart_session`

## State Notes

- This state model is inferred from discovered capabilities and workflow order.
- It is intended to scaffold runtime continuity and should not be interpreted as a proof of live production behavior.
- E-commerce flows are modeled with an in-memory cart-style session unless the generated server is integrated with durable storage.

## Tool Readiness Matrix

| Tool | Backend | Readiness | Verification | Approval | Session |
|---|---|---|---|---|---|
| `add_to_cart` | `api` | `route_mapped` | `structural` | `none` | `yes` |
| `apply_coupon` | `hybrid` | `structural_only` | `structural` | `none` | `no` |
| `calculate_shipping` | `hybrid` | `structural_only` | `structural` | `none` | `no` |
| `check_inventory` | `hybrid` | `structural_only` | `structural` | `none` | `no` |
| `get_business_info` | `browser` | `generated_browser` | `inferred` | `none` | `no` |
| `get_cart` | `api` | `route_mapped` | `structural` | `none` | `yes` |
| `get_order_status` | `api` | `route_mapped` | `structural` | `none` | `yes` |
| `get_product_details` | `api` | `route_mapped` | `structural` | `none` | `yes` |
| `initiate_return` | `hybrid` | `structural_only` | `structural` | `none` | `no` |
| `list_products` | `api` | `route_mapped` | `structural` | `none` | `yes` |
| `remove_from_cart` | `hybrid` | `structural_only` | `structural` | `none` | `yes` |
| `search_items` | `browser` | `generated_browser` | `inferred` | `confirmation_required` | `no` |
| `send_message` | `browser` | `generated_browser` | `inferred` | `confirmation_required` | `no` |
| `submit_checkout` | `api` | `route_mapped` | `structural` | `confirmation_required` | `yes` |

## Tool Notes

### `add_to_cart`

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### `apply_coupon`

- This capability is currently represented structurally and may need a site-specific executor before production use.

### `calculate_shipping`

- This capability is currently represented structurally and may need a site-specific executor before production use.

### `check_inventory`

- This capability is currently represented structurally and may need a site-specific executor before production use.

### `get_business_info`

- Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening.

### `get_cart`

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### `get_order_status`

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### `get_product_details`

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### `initiate_return`

- This capability is currently represented structurally and may need a site-specific executor before production use.

### `list_products`

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### `remove_from_cart`

- This capability is currently represented structurally and may need a site-specific executor before production use.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### `search_items`

- Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening.
- Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions.

### `send_message`

- Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening.
- Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions.

### `submit_checkout`

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.
- Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions.
