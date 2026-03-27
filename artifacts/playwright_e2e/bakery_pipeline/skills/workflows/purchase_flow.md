---
name: "purchase_flow"
description: "Complete purchase workflow: browse → cart → checkout → order tracking"
version: 0.1.0
transactional: true
steps: 6
---

# purchase_flow

Complete purchase workflow: browse → cart → checkout → order tracking

## Steps

1. **`list_products`** — List all products in the bakery catalog
2. **`get_product_details`** — Get full details for a specific product
3. **`add_to_cart`** — Add a product to the shopping cart
4. **`get_cart`** — Get current shopping cart contents
5. **`submit_checkout`** — Initiate checkout - returns payment URL for confirmation
6. **`get_order_status`** — Get order status and tracking info

## Data Flow

- `list_products.items[].id` → `add_to_cart.product_id`
- `get_product_details.id` → `add_to_cart.product_id`
- `add_to_cart.cart_id` → `get_cart.cart_id`
- `submit_checkout.order_id` → `get_order_status.orderId`
- `submit_checkout.checkout_id` → `get_order_status.orderId`

## Transaction Safety

This workflow is **transactional**. If any step fails, previous steps may need to be rolled back.
