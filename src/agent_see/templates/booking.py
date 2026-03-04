"""Service/booking capability templates for service businesses.

Covers service discovery, availability checking, appointment booking,
business info, quotes, and messaging — patterns seen in dental offices,
salons, plumbers, restaurants, and consultants.
"""

from __future__ import annotations

from agent_see.models.capability import (
    Capability,
    Parameter,
    ParameterType,
    ReturnField,
    ReturnSchema,
    SourceReference,
    SourceType,
)

TEMPLATE_CONFIDENCE = 0.65


def _make_source(location: str, snippet: str) -> SourceReference:
    return SourceReference(
        source_type=SourceType.TEMPLATE,
        location=location,
        raw_snippet=snippet,
    )


def get_services_template(source_url: str = "") -> Capability:
    """List all services offered by the business."""
    return Capability(
        id="tpl_get_services",
        name="get_services",
        description="List all services offered with pricing and details",
        source=_make_source(source_url, "Service business listing template"),
        parameters=[
            Parameter(
                name="category",
                param_type=ParameterType.STRING,
                description="Filter by service category",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="id", field_type="string", description="Service ID"),
                ReturnField(name="name", field_type="string", description="Service name"),
                ReturnField(name="description", field_type="string", description="Service description"),
                ReturnField(name="price", field_type="number", description="Service price"),
                ReturnField(name="currency", field_type="string", description="Currency code"),
                ReturnField(name="duration_minutes", field_type="integer", description="Service duration"),
                ReturnField(name="category", field_type="string", description="Service category"),
            ],
            is_array=True,
            description="List of available services",
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Service listing pattern detected"],
        idempotent=True,
        domain="services",
    )


def check_availability_template(source_url: str = "") -> Capability:
    """Check available time slots for a service."""
    return Capability(
        id="tpl_check_availability",
        name="check_availability",
        description="Check available time slots for a service on given dates",
        source=_make_source(source_url, "Availability check template"),
        parameters=[
            Parameter(
                name="service_id",
                param_type=ParameterType.STRING,
                description="Service identifier",
                required=True,
            ),
            Parameter(
                name="date_from",
                param_type=ParameterType.STRING,
                description="Start date (YYYY-MM-DD)",
                required=True,
            ),
            Parameter(
                name="date_to",
                param_type=ParameterType.STRING,
                description="End date (YYYY-MM-DD)",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="service_id", field_type="string", description="Service ID"),
                ReturnField(name="available_slots", field_type="array", description="Available time slots"),
                ReturnField(name="next_available", field_type="string", description="Next available date/time"),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Service availability check pattern detected"],
        idempotent=True,
        domain="booking",
    )


def book_appointment_template(source_url: str = "") -> Capability:
    """Book an appointment for a service."""
    return Capability(
        id="tpl_book_appointment",
        name="book_appointment",
        description="Book an appointment for a specific service and time",
        source=_make_source(source_url, "Appointment booking template"),
        parameters=[
            Parameter(
                name="service_id",
                param_type=ParameterType.STRING,
                description="Service identifier",
                required=True,
            ),
            Parameter(
                name="datetime",
                param_type=ParameterType.STRING,
                description="Appointment date and time (ISO 8601)",
                required=True,
            ),
            Parameter(
                name="customer_name",
                param_type=ParameterType.STRING,
                description="Customer full name",
                required=True,
            ),
            Parameter(
                name="customer_email",
                param_type=ParameterType.STRING,
                description="Customer email address",
                required=True,
            ),
            Parameter(
                name="customer_phone",
                param_type=ParameterType.STRING,
                description="Customer phone number",
                required=False,
            ),
            Parameter(
                name="notes",
                param_type=ParameterType.STRING,
                description="Additional notes or requests",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="booking_id", field_type="string", description="Booking confirmation ID"),
                ReturnField(name="status", field_type="string", description="Booking status"),
                ReturnField(name="service_name", field_type="string", description="Booked service name"),
                ReturnField(name="datetime", field_type="string", description="Confirmed date/time"),
                ReturnField(name="confirmation_url", field_type="string", description="Confirmation page URL"),
            ],
            is_array=False,
        ),
        side_effects=["creates_booking"],
        prerequisites=["available time slot required"],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Appointment booking pattern detected"],
        idempotent=False,
        domain="booking",
    )


def get_booking_status_template(source_url: str = "") -> Capability:
    """Check booking status."""
    return Capability(
        id="tpl_get_booking_status",
        name="get_booking_status",
        description="Get the current status of a booking",
        source=_make_source(source_url, "Booking status template"),
        parameters=[
            Parameter(
                name="booking_id",
                param_type=ParameterType.STRING,
                description="Booking identifier",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="booking_id", field_type="string", description="Booking ID"),
                ReturnField(name="status", field_type="string", description="Current status"),
                ReturnField(name="service_name", field_type="string", description="Service name"),
                ReturnField(name="datetime", field_type="string", description="Appointment date/time"),
                ReturnField(name="can_cancel", field_type="boolean", description="Whether booking can be cancelled"),
                ReturnField(name="can_reschedule", field_type="boolean", description="Whether booking can be rescheduled"),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=["valid booking_id required"],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Booking status pattern detected"],
        idempotent=True,
        domain="booking",
    )


def cancel_booking_template(source_url: str = "") -> Capability:
    """Cancel a booking."""
    return Capability(
        id="tpl_cancel_booking",
        name="cancel_booking",
        description="Cancel an existing booking",
        source=_make_source(source_url, "Booking cancellation template"),
        parameters=[
            Parameter(
                name="booking_id",
                param_type=ParameterType.STRING,
                description="Booking identifier",
                required=True,
            ),
            Parameter(
                name="reason",
                param_type=ParameterType.STRING,
                description="Reason for cancellation",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="booking_id", field_type="string", description="Booking ID"),
                ReturnField(name="status", field_type="string", description="Updated status"),
                ReturnField(name="refund_amount", field_type="number", description="Refund amount if applicable", nullable=True),
            ],
            is_array=False,
        ),
        side_effects=["cancels_booking"],
        prerequisites=["booking must be cancellable"],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Booking cancellation pattern detected"],
        idempotent=True,
        domain="booking",
    )


def get_business_info_template(source_url: str = "") -> Capability:
    """Get business information (location, hours, contact)."""
    return Capability(
        id="tpl_get_business_info",
        name="get_business_info",
        description="Get business location, hours, contact info, and service area",
        source=_make_source(source_url, "Business info template"),
        parameters=[],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="name", field_type="string", description="Business name"),
                ReturnField(name="address", field_type="string", description="Physical address"),
                ReturnField(name="phone", field_type="string", description="Phone number"),
                ReturnField(name="email", field_type="string", description="Contact email"),
                ReturnField(name="website", field_type="string", description="Website URL"),
                ReturnField(name="hours", field_type="object", description="Operating hours by day"),
                ReturnField(name="service_area", field_type="string", description="Geographic service area"),
                ReturnField(name="categories", field_type="array", description="Business categories/tags"),
            ],
            is_array=False,
        ),
        side_effects=[],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Business info pattern detected"],
        idempotent=True,
        domain="business",
    )


def request_quote_template(source_url: str = "") -> Capability:
    """Request a quote for custom/variable-price services."""
    return Capability(
        id="tpl_request_quote",
        name="request_quote",
        description="Request a price quote for a custom service",
        source=_make_source(source_url, "Quote request template"),
        parameters=[
            Parameter(
                name="service_id",
                param_type=ParameterType.STRING,
                description="Service identifier",
                required=True,
            ),
            Parameter(
                name="description",
                param_type=ParameterType.STRING,
                description="Description of what you need",
                required=True,
            ),
            Parameter(
                name="customer_name",
                param_type=ParameterType.STRING,
                description="Customer name",
                required=True,
            ),
            Parameter(
                name="customer_email",
                param_type=ParameterType.STRING,
                description="Customer email",
                required=True,
            ),
            Parameter(
                name="customer_phone",
                param_type=ParameterType.STRING,
                description="Customer phone number",
                required=False,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="quote_id", field_type="string", description="Quote request ID"),
                ReturnField(name="status", field_type="string", description="Quote request status"),
                ReturnField(name="estimated_response_hours", field_type="integer", description="Expected response time in hours"),
            ],
            is_array=False,
        ),
        side_effects=["creates_quote_request"],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Quote request pattern detected"],
        idempotent=False,
        domain="services",
    )


def send_message_template(source_url: str = "") -> Capability:
    """Send a message/inquiry to the business."""
    return Capability(
        id="tpl_send_message",
        name="send_message",
        description="Send a message or inquiry to the business",
        source=_make_source(source_url, "Contact/messaging template"),
        parameters=[
            Parameter(
                name="subject",
                param_type=ParameterType.STRING,
                description="Message subject",
                required=True,
            ),
            Parameter(
                name="body",
                param_type=ParameterType.STRING,
                description="Message body",
                required=True,
            ),
            Parameter(
                name="sender_name",
                param_type=ParameterType.STRING,
                description="Sender name",
                required=True,
            ),
            Parameter(
                name="sender_email",
                param_type=ParameterType.STRING,
                description="Sender email for reply",
                required=True,
            ),
        ],
        returns=ReturnSchema(
            fields=[
                ReturnField(name="message_id", field_type="string", description="Message ID"),
                ReturnField(name="status", field_type="string", description="Delivery status"),
            ],
            is_array=False,
        ),
        side_effects=["sends_message"],
        prerequisites=[],
        confidence=TEMPLATE_CONFIDENCE,
        evidence=["Contact form / messaging pattern detected"],
        idempotent=False,
        domain="contact",
    )


# All booking/service templates
BOOKING_TEMPLATES = [
    get_services_template,
    check_availability_template,
    book_appointment_template,
    get_booking_status_template,
    cancel_booking_template,
    get_business_info_template,
    request_quote_template,
    send_message_template,
]

# Indicators for service business patterns
BOOKING_INDICATORS = {
    "appointment", "book", "booking", "schedule", "availability",
    "service", "services", "consultation", "quote", "estimate",
    "hours", "contact us", "request appointment", "book now",
    "schedule appointment", "free estimate",
}


def detect_booking(page_text: str) -> bool:
    """Check if page text suggests a service/booking business."""
    text_lower = page_text.lower()
    matches = sum(1 for indicator in BOOKING_INDICATORS if indicator in text_lower)
    return matches >= 3


def get_booking_capabilities(source_url: str = "") -> list[Capability]:
    """Get all service/booking template capabilities."""
    return [tpl(source_url) for tpl in BOOKING_TEMPLATES]
