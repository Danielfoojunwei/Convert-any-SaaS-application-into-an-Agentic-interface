"""Extract capabilities from a live website using browser DOM analysis.

For SMB sites without APIs, this is the primary extraction path.
Uses Playwright to render pages and analyzes DOM structure to identify
interactive elements (forms, buttons, links) that represent capabilities.
"""

from __future__ import annotations

import logging
import re

from agent_see.discovery.page_crawler import (
    CrawlResult,
    FormField,
    FormInfo,
    PageInfo,
)
from agent_see.models.capability import (
    Capability,
    Parameter,
    ParameterType,
    ReturnSchema,
    SourceReference,
    SourceType,
)

logger = logging.getLogger(__name__)

# Map HTML input types to parameter types
INPUT_TYPE_MAP: dict[str, ParameterType] = {
    "text": ParameterType.STRING,
    "email": ParameterType.STRING,
    "tel": ParameterType.STRING,
    "url": ParameterType.STRING,
    "password": ParameterType.STRING,
    "search": ParameterType.STRING,
    "textarea": ParameterType.STRING,
    "number": ParameterType.NUMBER,
    "range": ParameterType.NUMBER,
    "date": ParameterType.STRING,
    "datetime-local": ParameterType.STRING,
    "time": ParameterType.STRING,
    "checkbox": ParameterType.BOOLEAN,
    "radio": ParameterType.ENUM,
    "select": ParameterType.ENUM,
    "file": ParameterType.STRING,
    "hidden": ParameterType.STRING,
}


def _form_field_to_parameter(field: FormField) -> Parameter:
    """Convert an HTML form field to a Capability parameter."""
    param_type = INPUT_TYPE_MAP.get(field.field_type, ParameterType.STRING)
    return Parameter(
        name=field.name.replace("-", "_").replace(" ", "_").lower(),
        param_type=param_type,
        description=field.label or f"The {field.name} field",
        required=field.required,
        enum_values=field.options if field.options else None,
    )


def _infer_capability_from_form(
    form: FormInfo,
    page: PageInfo,
    form_index: int,
) -> Capability | None:
    """Infer a capability from an HTML form.

    Forms are the primary way SMB sites expose capabilities:
    - Contact forms → send_message
    - Search forms → search_products
    - Booking forms → book_appointment
    - Checkout forms → place_order
    """
    if not form.fields:
        return None

    # Infer the capability type from form context
    field_names = {f.name.lower() for f in form.fields}
    submit_text = form.submit_text.lower()
    page_domain = page.domain_hint
    action_lower = form.action.lower()

    # Classify the form
    name: str
    description: str
    domain: str

    if any(w in submit_text for w in ("search", "find", "look")):
        name = "search_items"
        description = "Search for items on the site"
        domain = "search"
    elif any(w in submit_text for w in ("book", "schedule", "reserve")):
        name = "book_appointment"
        description = "Book an appointment or reservation"
        domain = "booking"
    elif any(w in submit_text for w in ("buy", "add to cart", "purchase", "order")):
        name = "add_to_cart"
        description = "Add an item to the shopping cart"
        domain = "cart"
    elif any(
        w in submit_text
        for w in ("contact", "send", "message", "submit inquiry")
    ):
        name = "send_message"
        description = "Send a message to the business"
        domain = "contact"
    elif any(w in submit_text for w in ("subscribe", "sign up", "join")):
        name = "subscribe"
        description = "Subscribe to the mailing list or service"
        domain = "account"
    elif any(w in submit_text for w in ("login", "sign in", "log in")):
        name = "authenticate"
        description = "Log in to an account"
        domain = "account"
    elif any(w in submit_text for w in ("register", "create account")):
        name = "create_account"
        description = "Create a new account"
        domain = "account"
    elif page_domain == "checkout" or "checkout" in action_lower:
        name = "submit_checkout"
        description = "Submit checkout/payment information"
        domain = "checkout"
    elif page_domain == "contact" or any(
        n in field_names for n in ("email", "message", "subject")
    ):
        name = "send_message"
        description = "Send a message to the business"
        domain = "contact"
    elif page_domain == "booking" or any(
        n in field_names for n in ("date", "time", "appointment")
    ):
        name = "book_appointment"
        description = "Book an appointment"
        domain = "booking"
    else:
        name = f"submit_form_{form_index}"
        description = f"Submit form on {page.title or page.url}"
        domain = page_domain or "general"

    # Convert form fields to parameters
    parameters = [_form_field_to_parameter(f) for f in form.fields if f.name]

    # Build evidence
    evidence = [
        f"Form found on page: {page.url}",
        f"Form action: {form.action}",
        f"Form method: {form.method}",
        f"Submit button text: {form.submit_text}",
        f"Fields: {', '.join(f.name for f in form.fields)}",
    ]

    cap_id = f"browser_form_{domain}_{name}"

    return Capability(
        id=cap_id,
        name=name,
        description=description,
        source=SourceReference(
            source_type=SourceType.BROWSER_DOM,
            location=f"{page.url}#form[{form_index}]",
            raw_snippet=f"<form action='{form.action}' method='{form.method}'> "
            f"fields: {', '.join(f.name for f in form.fields)} "
            f"submit: '{form.submit_text}'",
            url=page.url,
        ),
        parameters=parameters,
        returns=ReturnSchema(description="Form submission result"),
        side_effects=[f"Submits form to {form.action}"] if form.action else [],
        prerequisites=[],
        confidence=0.7,  # Browser DOM extraction
        evidence=evidence,
        idempotent=form.method.upper() == "GET",
        domain=domain,
    )


def _infer_product_listing(page: PageInfo) -> Capability | None:
    """Detect product listing capabilities from page content patterns."""
    html_lower = page.html_content.lower()

    # Check for product-like patterns
    product_indicators = [
        "product-card",
        "product-item",
        "product-grid",
        "product-list",
        "price",
        "add-to-cart",
        "add to cart",
        "shop-item",
    ]

    matches = sum(1 for ind in product_indicators if ind in html_lower)
    if matches < 2:
        return None

    # Count approximate number of products
    price_count = len(re.findall(r"\$\d+", page.html_content))

    evidence = [
        f"Product listing page: {page.url}",
        f"Page title: {page.title}",
        f"Product indicators found: {matches}",
        f"Price mentions: {price_count}",
    ]

    return Capability(
        id=f"browser_list_products_{page.domain_hint}",
        name="list_products",
        description="Browse the product catalog",
        source=SourceReference(
            source_type=SourceType.BROWSER_DOM,
            location=page.url,
            raw_snippet=f"Product listing page with {price_count} prices detected",
            url=page.url,
        ),
        parameters=[
            Parameter(
                name="page",
                param_type=ParameterType.INTEGER,
                description="Page number for pagination",
                required=False,
                default=1,
            ),
        ],
        returns=ReturnSchema(
            description="List of products with names, prices, and IDs",
            is_array=True,
        ),
        confidence=0.7,
        evidence=evidence,
        idempotent=True,
        domain="products",
    )


def extract_from_crawl(crawl_result: CrawlResult) -> list[Capability]:
    """Extract capabilities from a website crawl result.

    Analyzes pages, forms, and content patterns to identify capabilities.

    Args:
        crawl_result: The result of crawling the website

    Returns:
        List of Capabilities with evidence from DOM analysis
    """
    capabilities: list[Capability] = []
    seen_names: set[str] = set()

    for page in crawl_result.pages:
        # Extract capabilities from forms
        for i, form in enumerate(page.forms):
            cap = _infer_capability_from_form(form, page, i)
            if cap and cap.name not in seen_names:
                capabilities.append(cap)
                seen_names.add(cap.name)

        # Detect product listing pages
        if page.domain_hint == "products":
            cap = _infer_product_listing(page)
            if cap and cap.name not in seen_names:
                capabilities.append(cap)
                seen_names.add(cap.name)

    # Add business info capability if we found an about or contact page
    if "about" in crawl_result.domain_pages or "contact" in crawl_result.domain_pages:
        about_url = ""
        if "about" in crawl_result.domain_pages:
            about_url = crawl_result.domain_pages["about"][0]
        elif "contact" in crawl_result.domain_pages:
            about_url = crawl_result.domain_pages["contact"][0]

        if "get_business_info" not in seen_names:
            capabilities.append(
                Capability(
                    id="browser_get_business_info",
                    name="get_business_info",
                    description="Get business contact information, hours, and location",
                    source=SourceReference(
                        source_type=SourceType.BROWSER_DOM,
                        location=about_url,
                        raw_snippet="About/contact page found on site",
                        url=about_url,
                    ),
                    parameters=[],
                    returns=ReturnSchema(
                        description="Business name, address, phone, hours, email"
                    ),
                    confidence=0.7,
                    evidence=[f"About/contact page found at: {about_url}"],
                    idempotent=True,
                    domain="info",
                )
            )

    logger.info(
        f"Extracted {len(capabilities)} capabilities from browser crawl "
        f"({crawl_result.total_pages} pages, {crawl_result.total_forms} forms)"
    )
    return capabilities
