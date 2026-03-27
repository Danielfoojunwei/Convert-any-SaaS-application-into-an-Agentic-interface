"""Capability graph construction and workflow inference.

Takes raw capabilities from any extractor and structures them into
a graph with domains, relationships, and workflows.
"""

from __future__ import annotations

import logging

from agent_see.models.capability import (
    AuthModel,
    AuthType,
    Capability,
    CapabilityEdge,
    CapabilityGraph,
    Domain,
    EdgeType,
    StateModel,
    Workflow,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

# Standard e-commerce workflow
ECOMMERCE_WORKFLOW_PATTERN = [
    "list_products",
    "get_product_details",
    "add_to_cart",
    "get_cart",
    "submit_checkout",
    "get_order_status",
]

# Standard booking workflow
BOOKING_WORKFLOW_PATTERN = [
    "get_services",
    "check_availability",
    "book_appointment",
    "get_booking_status",
]


def _group_by_domain(capabilities: list[Capability]) -> dict[str, list[Capability]]:
    """Group capabilities by their domain."""
    domains: dict[str, list[Capability]] = {}
    for cap in capabilities:
        domain = cap.domain or "general"
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(cap)
    return domains


def _find_matching_cap(
    caps: dict[str, Capability], verb: str, noun_root: str
) -> Capability | None:
    """Find a capability matching verb + noun root with light fuzzy matching."""
    exact = f"{verb}_{noun_root}"
    if exact in caps:
        return caps[exact]

    for name, cap in caps.items():
        parts = name.split("_", 1)
        if len(parts) >= 2 and parts[0] == verb:
            cap_noun = parts[1]
            if cap_noun.startswith(noun_root) or noun_root.startswith(cap_noun):
                return cap
    return None


def _infer_edges(capabilities: list[Capability]) -> list[CapabilityEdge]:
    """Infer relationships between capabilities based on naming and domain patterns."""
    edges: list[CapabilityEdge] = []
    cap_by_name: dict[str, Capability] = {c.name: c for c in capabilities}

    for cap in capabilities:
        name_parts = cap.name.split("_", 1)
        if len(name_parts) < 2:
            continue
        verb, noun = name_parts[0], name_parts[1]
        noun_root = noun.rstrip("s") if noun.endswith("s") and len(noun) > 2 else noun

        if verb == "get":
            for other_verb in ("update", "delete"):
                match = _find_matching_cap(cap_by_name, other_verb, noun_root)
                if match and match.id != cap.id:
                    edges.append(
                        CapabilityEdge(
                            source_id=cap.id,
                            target_id=match.id,
                            edge_type=EdgeType.PRODUCES_INPUT_FOR,
                            description=f"{cap.name} provides data for {match.name}",
                        )
                    )

        if verb == "list":
            match = _find_matching_cap(cap_by_name, "get", noun_root)
            if match and match.id != cap.id:
                edges.append(
                    CapabilityEdge(
                        source_id=cap.id,
                        target_id=match.id,
                        edge_type=EdgeType.PRODUCES_INPUT_FOR,
                        description=f"{cap.name} provides IDs for {match.name}",
                    )
                )

        if verb == "create":
            match = _find_matching_cap(cap_by_name, "get", noun_root)
            if match and match.id != cap.id:
                edges.append(
                    CapabilityEdge(
                        source_id=cap.id,
                        target_id=match.id,
                        edge_type=EdgeType.PRODUCES_INPUT_FOR,
                        description=f"{cap.name} creates resource for {match.name}",
                    )
                )

    if "add_to_cart" in cap_by_name and "submit_checkout" in cap_by_name:
        edges.append(
            CapabilityEdge(
                source_id=cap_by_name["add_to_cart"].id,
                target_id=cap_by_name["submit_checkout"].id,
                edge_type=EdgeType.PRODUCES_INPUT_FOR,
                description="Cart must have items before checkout",
            )
        )

    if "list_products" in cap_by_name and "add_to_cart" in cap_by_name:
        edges.append(
            CapabilityEdge(
                source_id=cap_by_name["list_products"].id,
                target_id=cap_by_name["add_to_cart"].id,
                edge_type=EdgeType.PRODUCES_INPUT_FOR,
                description="Need product IDs to add to cart",
            )
        )

    if "check_availability" in cap_by_name and "book_appointment" in cap_by_name:
        edges.append(
            CapabilityEdge(
                source_id=cap_by_name["check_availability"].id,
                target_id=cap_by_name["book_appointment"].id,
                edge_type=EdgeType.PRODUCES_INPUT_FOR,
                description="Availability must be checked before booking",
            )
        )

    return edges


def _detect_workflows(capabilities: list[Capability]) -> list[Workflow]:
    """Detect multi-step workflows from capability patterns."""
    workflows: list[Workflow] = []
    cap_names = {c.name for c in capabilities}
    cap_by_name = {c.name: c for c in capabilities}

    ecom_steps = [n for n in ECOMMERCE_WORKFLOW_PATTERN if n in cap_names]
    if len(ecom_steps) >= 3:
        steps: list[WorkflowStep] = []
        for idx, name in enumerate(ecom_steps):
            output_maps_to: dict[str, str] = {}
            if name == "list_products" and "add_to_cart" in cap_names:
                output_maps_to["items[].id"] = "add_to_cart.product_id"
            if name == "get_product_details" and "add_to_cart" in cap_names:
                output_maps_to["id"] = "add_to_cart.product_id"
            if name == "add_to_cart" and "get_cart" in cap_names:
                output_maps_to["cart_id"] = "get_cart.cart_id"
            if name == "submit_checkout" and "get_order_status" in cap_names:
                output_maps_to["order_id"] = "get_order_status.orderId"
                output_maps_to["checkout_id"] = "get_order_status.orderId"

            steps.append(
                WorkflowStep(
                    capability_id=cap_by_name[name].id,
                    description=cap_by_name[name].description,
                    output_maps_to=output_maps_to,
                )
            )

        workflows.append(
            Workflow(
                name="purchase_flow",
                description="Complete purchase workflow: browse → cart → checkout → order tracking",
                steps=steps,
                is_transactional=True,
                requires_session=True,
                operational_notes=[
                    "State transitions are inferred from discovered capabilities rather than live checkout instrumentation.",
                    "Generated runtime can scaffold session continuity, but durable persistence still requires production storage.",
                ],
            )
        )

    booking_steps = [n for n in BOOKING_WORKFLOW_PATTERN if n in cap_names]
    if len(booking_steps) >= 2:
        steps = []
        for name in booking_steps:
            booking_output_maps_to: dict[str, str] = {}
            if name == "get_services" and "check_availability" in cap_names:
                booking_output_maps_to["items[].service_id"] = "check_availability.service_id"
            if name == "check_availability" and "book_appointment" in cap_names:
                booking_output_maps_to["available_slots[].start_time"] = "book_appointment.start_time"
            if name == "book_appointment" and "get_booking_status" in cap_names:
                booking_output_maps_to["booking_id"] = "get_booking_status.booking_id"

            steps.append(
                WorkflowStep(
                    capability_id=cap_by_name[name].id,
                    description=cap_by_name[name].description,
                    output_maps_to=booking_output_maps_to,
                )
            )

        workflows.append(
            Workflow(
                name="booking_flow",
                description="Service booking workflow: browse → availability → reservation tracking",
                steps=steps,
                is_transactional=True,
                requires_session=True,
                operational_notes=[
                    "Booking-state transitions are inferred from capability names and parameter flow.",
                    "Human review may still be appropriate for identity, insurance, or payment details.",
                ],
            )
        )

    return workflows


def _infer_auth_model(capabilities: list[Capability]) -> AuthModel:
    """Infer authentication requirements from capability sources."""
    for cap in capabilities:
        if any(p.name in ("api_key", "token", "authorization") for p in cap.parameters):
            return AuthModel(
                auth_type=AuthType.API_KEY,
                description="API key authentication detected",
            )
        if any("oauth" in p.name.lower() for p in cap.parameters):
            return AuthModel(
                auth_type=AuthType.OAUTH2,
                description="OAuth2 authentication detected",
            )

    for cap in capabilities:
        if any("auth" in p.lower() or "login" in p.lower() for p in cap.prerequisites):
            return AuthModel(
                auth_type=AuthType.SESSION_COOKIE,
                description="Session-based authentication detected",
            )

    return AuthModel(auth_type=AuthType.NONE)


def _infer_state_model(
    capabilities: list[Capability], workflows: list[Workflow]
) -> StateModel:
    """Infer starter-grade runtime state scaffolding from workflows and domains."""
    cap_names = {c.name for c in capabilities}
    states: dict[str, list[str]] = {}
    workflow_states: dict[str, list[str]] = {}
    session_entities: list[str] = []
    operational_notes: list[str] = [
        "This state model is inferred from discovered capabilities and workflow order.",
        "It is intended to scaffold runtime continuity and should not be interpreted as a proof of live production behavior.",
    ]

    if any(name in cap_names for name in ("add_to_cart", "get_cart", "submit_checkout", "get_order_status")):
        states.update(
            {
                "browsing": ["cart_review"],
                "cart_review": ["checkout_ready", "browsing"],
                "checkout_ready": ["payment_pending", "cart_review"],
                "payment_pending": ["order_tracking"],
                "order_tracking": [],
            }
        )
        workflow_states["purchase_flow"] = [
            "browsing",
            "cart_review",
            "checkout_ready",
            "payment_pending",
            "order_tracking",
        ]
        session_entities.append("cart_session")
        operational_notes.append(
            "E-commerce flows are modeled with an in-memory cart-style session unless the generated server is integrated with durable storage."
        )

    if any(name in cap_names for name in ("check_availability", "book_appointment", "get_booking_status")):
        states.update(
            {
                "service_selection": ["availability_checked"],
                "availability_checked": ["booking_pending", "service_selection"],
                "booking_pending": ["booking_confirmed"],
                "booking_confirmed": [],
            }
        )
        workflow_states["booking_flow"] = [
            "service_selection",
            "availability_checked",
            "booking_pending",
            "booking_confirmed",
        ]
        session_entities.append("booking_session")
        operational_notes.append(
            "Booking flows may require user identity, timing, or policy confirmation beyond the inferred state machine."
        )

    for workflow in workflows:
        if workflow.requires_session and workflow.name not in workflow_states:
            workflow_states[workflow.name] = [step.capability_id for step in workflow.steps]

    description = (
        "Starter-grade runtime state model inferred from workflow structure. "
        "Useful for generated execution scaffolding, approvals, and session continuity."
    )

    return StateModel(
        states=states,
        workflow_states=workflow_states,
        session_entities=session_entities,
        operational_notes=operational_notes,
        description=description,
    )


def build_capability_graph(
    capabilities: list[Capability],
    source_url: str | None = None,
) -> CapabilityGraph:
    """Build a structured CapabilityGraph from extracted capabilities."""
    seen: dict[str, Capability] = {}
    for cap in capabilities:
        if cap.name not in seen or cap.confidence > seen[cap.name].confidence:
            seen[cap.name] = cap
    deduped = list(seen.values())

    nodes = {cap.id: cap for cap in deduped}

    domain_groups = _group_by_domain(deduped)
    domains = [
        Domain(
            name=domain_name,
            description=f"Capabilities related to {domain_name}",
            capability_ids=[c.id for c in caps],
        )
        for domain_name, caps in domain_groups.items()
    ]

    edges = _infer_edges(deduped)
    workflows = _detect_workflows(deduped)
    auth_model = _infer_auth_model(deduped)
    state_model = _infer_state_model(deduped, workflows)

    graph = CapabilityGraph(
        nodes=nodes,
        edges=edges,
        domains=domains,
        workflows=workflows,
        auth_model=auth_model,
        state_model=state_model,
        source_url=source_url,
    )

    graph.source_hash = graph.compute_source_hash()

    logger.info(
        f"Built capability graph: {graph.capability_count} capabilities, "
        f"{len(domains)} domains, {len(edges)} edges, {len(workflows)} workflows"
    )

    return graph
