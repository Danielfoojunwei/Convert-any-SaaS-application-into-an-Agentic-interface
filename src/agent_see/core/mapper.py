"""Build a CapabilityGraph from extracted capabilities.

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
    """Find a capability matching verb + noun root (flexible matching).

    Handles cases like: noun_root='pet' matches 'delete_pet', 'get_pet_by_id', etc.
    """
    # Exact match first
    exact = f"{verb}_{noun_root}"
    if exact in caps:
        return caps[exact]

    # Fuzzy: find any cap starting with verb_ that contains the noun root
    for name, cap in caps.items():
        parts = name.split("_", 1)
        if len(parts) >= 2 and parts[0] == verb:
            cap_noun = parts[1]
            # Check if noun root is a prefix/substring
            if cap_noun.startswith(noun_root) or noun_root.startswith(cap_noun):
                return cap
    return None


def _infer_edges(capabilities: list[Capability]) -> list[CapabilityEdge]:
    """Infer relationships between capabilities based on naming and domain patterns."""
    edges: list[CapabilityEdge] = []
    cap_by_name: dict[str, Capability] = {c.name: c for c in capabilities}

    # Also index by domain for cross-domain relationships
    domain_caps: dict[str, list[Capability]] = {}
    for cap in capabilities:
        if cap.domain not in domain_caps:
            domain_caps[cap.domain] = []
        domain_caps[cap.domain].append(cap)

    for cap in capabilities:
        name_parts = cap.name.split("_", 1)
        if len(name_parts) < 2:
            continue
        verb, noun = name_parts[0], name_parts[1]

        # Derive the singular noun root (e.g., "pets" → "pet")
        noun_root = noun.rstrip("s") if noun.endswith("s") and len(noun) > 2 else noun

        # get_X produces_input_for update_X and delete_X
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

        # list_X produces_input_for get_X (list returns IDs that get uses)
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

        # create_X → same domain get/list can use the created resource
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

    # E-commerce specific edges
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

    return edges


def _detect_workflows(
    capabilities: list[Capability],
) -> list[Workflow]:
    """Detect multi-step workflows from capability patterns."""
    workflows: list[Workflow] = []
    cap_names = {c.name for c in capabilities}
    cap_by_name = {c.name: c for c in capabilities}

    # Check for e-commerce workflow
    ecom_steps = [n for n in ECOMMERCE_WORKFLOW_PATTERN if n in cap_names]
    if len(ecom_steps) >= 3:  # At least list, add_to_cart, checkout
        workflows.append(
            Workflow(
                name="purchase_flow",
                description="Complete purchase workflow: browse → cart → checkout",
                steps=[
                    WorkflowStep(
                        capability_id=cap_by_name[name].id,
                        description=cap_by_name[name].description,
                    )
                    for name in ecom_steps
                ],
                is_transactional=True,
            )
        )

    # Check for booking workflow
    booking_steps = [n for n in BOOKING_WORKFLOW_PATTERN if n in cap_names]
    if len(booking_steps) >= 2:
        workflows.append(
            Workflow(
                name="booking_flow",
                description="Service booking workflow: browse → check availability → book",
                steps=[
                    WorkflowStep(
                        capability_id=cap_by_name[name].id,
                        description=cap_by_name[name].description,
                    )
                    for name in booking_steps
                ],
                is_transactional=True,
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

    # Check if any capability has auth-related prerequisites
    for cap in capabilities:
        if any("auth" in p.lower() or "login" in p.lower() for p in cap.prerequisites):
            return AuthModel(
                auth_type=AuthType.SESSION_COOKIE,
                description="Session-based authentication detected",
            )

    return AuthModel(auth_type=AuthType.NONE)


def build_capability_graph(
    capabilities: list[Capability],
    source_url: str | None = None,
) -> CapabilityGraph:
    """Build a structured CapabilityGraph from a list of extracted capabilities.

    This organizes raw capabilities into domains, infers relationships,
    detects multi-step workflows, and determines auth requirements.

    Args:
        capabilities: List of capabilities from any extractor
        source_url: URL of the original site

    Returns:
        A complete CapabilityGraph ready for code generation
    """
    # Deduplicate by name (keep highest confidence)
    seen: dict[str, Capability] = {}
    for cap in capabilities:
        if cap.name not in seen or cap.confidence > seen[cap.name].confidence:
            seen[cap.name] = cap
    deduped = list(seen.values())

    # Build nodes dict
    nodes = {cap.id: cap for cap in deduped}

    # Group into domains
    domain_groups = _group_by_domain(deduped)
    domains = [
        Domain(
            name=domain_name,
            description=f"Capabilities related to {domain_name}",
            capability_ids=[c.id for c in caps],
        )
        for domain_name, caps in domain_groups.items()
    ]

    # Infer edges
    edges = _infer_edges(deduped)

    # Detect workflows
    workflows = _detect_workflows(deduped)

    # Infer auth model
    auth_model = _infer_auth_model(deduped)

    graph = CapabilityGraph(
        nodes=nodes,
        edges=edges,
        domains=domains,
        workflows=workflows,
        auth_model=auth_model,
        state_model=StateModel(),
        source_url=source_url,
    )

    # Compute source hash for provenance
    graph.source_hash = graph.compute_source_hash()

    logger.info(
        f"Built capability graph: {graph.capability_count} capabilities, "
        f"{len(domains)} domains, {len(edges)} edges, {len(workflows)} workflows"
    )

    return graph
