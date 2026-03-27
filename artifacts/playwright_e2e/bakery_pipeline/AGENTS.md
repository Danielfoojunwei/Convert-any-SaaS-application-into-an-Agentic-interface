---
name: "http://127.0.0.1:43987"
description: "Agent-optimized interface for http://127.0.0.1:43987"
version: 0.1.0
tools: 14
---

# Agent Interface: http://127.0.0.1:43987

This interface provides 14 tools across 7 domains for interacting with http://127.0.0.1:43987. The generated interface is intentionally explicit about **operational readiness**: some tools are route-mapped or browser-generated, while others still require additional hardening before they should be treated as production-ready automation.

## Quick Reference

| Tool | Description | Domain | Readiness | Approval |
|------|-------------|--------|-----------|----------|
| `add_to_cart` | Add a product to the shopping cart | cart | `route_mapped` | `none` |
| `apply_coupon` | Apply a coupon or discount code to the cart | cart | `structural_only` | `none` |
| `calculate_shipping` | Calculate shipping options and costs for delivery address | checkout | `structural_only` | `none` |
| `check_inventory` | Check real-time stock status for a product variant | products | `structural_only` | `none` |
| `get_business_info` | Get business contact information, hours, and location | info | `generated_browser` | `none` |
| `get_cart` | Get current shopping cart contents | cart | `route_mapped` | `none` |
| `get_order_status` | Get order status and tracking info | orders | `route_mapped` | `none` |
| `get_product_details` | Get full details for a specific product | products | `route_mapped` | `none` |
| `initiate_return` | Start a return or refund request for an order | orders | `structural_only` | `none` |
| `list_products` | List all products in the bakery catalog | products | `route_mapped` | `none` |
| `remove_from_cart` | Remove a product from the shopping cart | cart | `structural_only` | `none` |
| `search_items` | Search for items on the site | search | `generated_browser` | `confirmation_required` |
| `send_message` | Send a message to the business | contact | `generated_browser` | `confirmation_required` |
| `submit_checkout` | Initiate checkout - returns payment URL for confirmation | checkout | `route_mapped` | `confirmation_required` |

## Operational Posture

| Signal | Meaning |
|--------|---------|
| `route_mapped` | The tool has a grounded API route and structured request mapping. |
| `generated_browser` | The tool has generated browser automation scaffolding derived from discovered UI evidence. |
| `structural_only` | The tool exists in the interface contract but still needs a more site-specific executor. |
| `structural` verification | The generator proved the interface mapping, not a live execution trace. |
| `inferred` verification | The runtime path is inferred from DOM or network evidence and may need hardening. |
| `live_verified` verification | A live execution path has been empirically verified. |

## Runtime State Model

Starter-grade runtime state model inferred from workflow structure. Useful for generated execution scaffolding, approvals, and session continuity.

| Workflow | Inferred States |
|----------|-----------------|
| `purchase_flow` | browsing → cart_review → checkout_ready → payment_pending → order_tracking |

Stateful entities that may need persistence:

- `cart_session`

> This state model is inferred from discovered capabilities and workflow order.
> It is intended to scaffold runtime continuity and should not be interpreted as a proof of live production behavior.
> E-commerce flows are modeled with an in-memory cart-style session unless the generated server is integrated with durable storage.

## Tools by Domain

### Cart

#### `add_to_cart`

Add a product to the shopping cart

| Property | Value |
|----------|-------|
| Idempotent | No |
| Backend | `api` |
| Readiness | `route_mapped` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `yes` |

**Parameters:**

- `product_id` (string, required): Product identifier
- `quantity` (integer, required): Number of items to add
- `variant_id` (string, optional): Product variant (size, flavor)

**Returns:**

- `cart_id` (string): 
- `items` (array): 
- `item_count` (integer): 
- `subtotal` (number): 
- `currency` (string): 

**Operational Notes:**

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

#### `apply_coupon`

Apply a coupon or discount code to the cart

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `hybrid` |
| Readiness | `structural_only` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `no` |

**Parameters:**

- `code` (string, required): Coupon or discount code

**Returns:**

- `applied` (boolean): Whether the code was accepted
- `discount_amount` (number): Discount amount
- `new_subtotal` (number): Cart subtotal after discount
- `message` (string): Coupon status message

**Operational Notes:**

- This capability is currently represented structurally and may need a site-specific executor before production use.

#### `get_cart`

Get current shopping cart contents

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `api` |
| Readiness | `route_mapped` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `yes` |

**Returns:**

- `cart_id` (string): 
- `items` (array): 
- `item_count` (integer): 
- `subtotal` (number): 
- `currency` (string): 

**Operational Notes:**

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

#### `remove_from_cart`

Remove a product from the shopping cart

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `hybrid` |
| Readiness | `structural_only` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `yes` |

**Parameters:**

- `product_id` (string, required): Product identifier to remove
- `variant_id` (string, optional): Specific variant to remove

**Returns:**

- `cart_id` (string): Cart session ID
- `item_count` (integer): Remaining items
- `subtotal` (number): Updated subtotal

**Operational Notes:**

- This capability is currently represented structurally and may need a site-specific executor before production use.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### Checkout

#### `calculate_shipping`

Calculate shipping options and costs for delivery address

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `hybrid` |
| Readiness | `structural_only` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `no` |

**Parameters:**

- `zip_code` (string, required): Delivery ZIP/postal code
- `country` (string, optional): Delivery country code (ISO 3166-1 alpha-2)

**Returns:**

- `options` (array): Available shipping options
- `cheapest_option` (object): Lowest cost option
- `fastest_option` (object): Fastest delivery option

**Operational Notes:**

- This capability is currently represented structurally and may need a site-specific executor before production use.

#### `submit_checkout`

Initiate checkout - returns payment URL for confirmation

| Property | Value |
|----------|-------|
| Idempotent | No |
| Backend | `api` |
| Readiness | `route_mapped` |
| Verification | `structural` |
| Approval | `confirmation_required` |
| Session Required | `yes` |

**Parameters:**

- `shipping_address` (object, required): Delivery address
- `email` (string, required): Customer email for confirmation
- `shipping_method` (string, optional): Selected shipping method
- `full_name` (string, required): Full Name
- `address` (string, required): Shipping Address
- `zip_code` (string, required): ZIP Code

**Returns:**

- `checkout_id` (string): 
- `payment_url` (string): 
- `total` (number): 
- `currency` (string): 
- `expires_at` (string): When this checkout session expires

**Operational Notes:**

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.
- Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions.

### Contact

#### `send_message`

Send a message to the business

| Property | Value |
|----------|-------|
| Idempotent | No |
| Backend | `browser` |
| Readiness | `generated_browser` |
| Verification | `inferred` |
| Approval | `confirmation_required` |
| Session Required | `no` |

**Parameters:**

- `sender_name` (string, required): Your Name
- `sender_email` (string, required): Your Email
- `subject` (string, required): Subject
- `body` (string, required): Your Message

**Operational Notes:**

- Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening.
- Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions.

### Info

#### `get_business_info`

Get business contact information, hours, and location

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `browser` |
| Readiness | `generated_browser` |
| Verification | `inferred` |
| Approval | `none` |
| Session Required | `no` |

**Operational Notes:**

- Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening.

### Orders

#### `get_order_status`

Get order status and tracking info

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `api` |
| Readiness | `route_mapped` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `yes` |

**Parameters:**

- `orderId` (string, required): Order identifier
- `order_id` (string, required): Order identifier

**Returns:**

- `order_id` (string): 
- `status` (string): 
- `items` (array): 
- `total` (number): 
- `tracking_number` (string): 
- `tracking_url` (string): Tracking URL
- `estimated_delivery` (string): Estimated delivery date

**Operational Notes:**

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

#### `initiate_return`

Start a return or refund request for an order

| Property | Value |
|----------|-------|
| Idempotent | No |
| Backend | `hybrid` |
| Readiness | `structural_only` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `no` |

**Parameters:**

- `order_id` (string, required): Order identifier
- `item_ids` (array, required): List of item IDs to return
- `reason` (string, required): Reason for return

**Returns:**

- `return_id` (string): Return request ID
- `status` (string): Return request status
- `return_label_url` (string): Return shipping label URL
- `refund_amount` (number): Expected refund amount

**Operational Notes:**

- This capability is currently represented structurally and may need a site-specific executor before production use.

### Products

#### `check_inventory`

Check real-time stock status for a product variant

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `hybrid` |
| Readiness | `structural_only` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `no` |

**Parameters:**

- `product_id` (string, required): Product identifier
- `variant_id` (string, optional): Specific variant (size, color)

**Returns:**

- `product_id` (string): Product ID
- `in_stock` (boolean): Whether in stock
- `quantity` (integer): Available quantity
- `restock_date` (string): Expected restock date

**Operational Notes:**

- This capability is currently represented structurally and may need a site-specific executor before production use.

#### `get_product_details`

Get full details for a specific product

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `api` |
| Readiness | `route_mapped` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `yes` |

**Parameters:**

- `productId` (string, required): Product identifier
- `product_id` (string, required): Product identifier

**Returns:**

- `id` (string): 
- `name` (string): 
- `description` (string): 
- `price` (number): 
- `currency` (string): 
- `category` (string): 
- `in_stock` (boolean): 
- `images` (array): 
- `variants` (array): Product variants (size, color, etc.)

**Operational Notes:**

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

#### `list_products`

List all products in the bakery catalog

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `api` |
| Readiness | `route_mapped` |
| Verification | `structural` |
| Approval | `none` |
| Session Required | `yes` |

**Parameters:**

- `category` (string, optional): Filter by product category
  - Allowed values: cakes, pastries, bread, custom
- `limit` (integer, optional): Number of results per page
- `page` (integer, optional): Page number for pagination
- `query` (string, optional): Search query for products
- `min_price` (number, optional): Minimum price filter
- `max_price` (number, optional): Maximum price filter

**Returns:**

- `id` (string): 
- `name` (string): 
- `description` (string): 
- `price` (number): 
- `currency` (string): 
- `category` (string): 
- `in_stock` (boolean): 
- `images` (array): 
- `image_url` (string): Product image URL

**Operational Notes:**

- Execution path is grounded in a discovered API route, but it has not been marked as live-verified by the generator.
- This tool participates in stateful execution and may depend on cookies, session continuity, or persisted workflow context.

### Search

#### `search_items`

Search for items on the site

| Property | Value |
|----------|-------|
| Idempotent | Yes |
| Backend | `browser` |
| Readiness | `generated_browser` |
| Verification | `inferred` |
| Approval | `confirmation_required` |
| Session Required | `no` |

**Parameters:**

- `query` (string, optional): Search products...

**Operational Notes:**

- Browser execution is generated from discovered DOM or network evidence and may require site-specific selector hardening.
- Human confirmation should be required before executing irreversible, payment-related, or identity-sensitive actions.

## Workflows

### Purchase Flow

Complete purchase workflow: browse → cart → checkout → order tracking

| Property | Value |
|----------|-------|
| Transactional | `yes` |
| Session Required | `yes` |

1. `list_products` — List all products in the bakery catalog
2. `get_product_details` — Get full details for a specific product
3. `add_to_cart` — Add a product to the shopping cart
4. `get_cart` — Get current shopping cart contents
5. `submit_checkout` — Initiate checkout - returns payment URL for confirmation
6. `get_order_status` — Get order status and tracking info

> State transitions are inferred from discovered capabilities rather than live checkout instrumentation.
> Generated runtime can scaffold session continuity, but durable persistence still requires production storage.

> This workflow involves a transaction. Payment or similarly irreversible actions should require human confirmation.

## Authentication

Type: `none`

## Error Handling

All tools return typed errors with recovery strategies:

| Error Code | Recovery | Retryable |
|------------|----------|-----------|
| `NOT_FOUND` | Fix parameters | No |
| `AUTH_FAILED` | Re-authenticate | No |
| `RATE_LIMITED` | Retry with backoff | Yes |
| `INVALID_PARAM` | Fix parameters | No |
| `SERVER_ERROR` | Retry | Yes |
| `TIMEOUT` | Retry with backoff | Yes |
| `PAYMENT_REQUIRED` | Human intervention | No |
