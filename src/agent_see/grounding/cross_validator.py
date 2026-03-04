"""Cross-validation engine for merging capabilities from multiple extractors.

When multiple extractors find the same capability, confidence increases.
When only one finds it, it's flagged for review. Conflicting extractions
are resolved by preferring higher-confidence sources.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from agent_see.models.capability import Capability, SourceType

logger = logging.getLogger(__name__)

# Confidence boost when multiple extractors agree
CROSS_VALIDATION_BOOST = 0.1

# Maximum confidence after boosting
MAX_CONFIDENCE = 1.0

# Minimum confidence to keep a capability
MIN_CONFIDENCE_THRESHOLD = 0.3


@dataclass
class MergeResult:
    """Result of merging capabilities from multiple extractors."""

    merged: list[Capability]
    duplicates_resolved: int = 0
    confidence_boosted: int = 0
    low_confidence_dropped: int = 0
    sources_per_capability: dict[str, list[SourceType]] = field(default_factory=dict)


def _capability_similarity(a: Capability, b: Capability) -> float:
    """Compute similarity between two capabilities.

    Uses name matching and parameter overlap.
    """
    # Exact name match
    if a.name == b.name:
        return 1.0

    # Check if names share the same verb and noun root
    a_parts = a.name.split("_", 1)
    b_parts = b.name.split("_", 1)

    if len(a_parts) < 2 or len(b_parts) < 2:
        return 0.0

    if a_parts[0] != b_parts[0]:
        return 0.0

    # Same verb, check noun similarity
    a_noun = a_parts[1].rstrip("s")
    b_noun = b_parts[1].rstrip("s")

    if a_noun == b_noun:
        return 0.9

    if a_noun.startswith(b_noun) or b_noun.startswith(a_noun):
        return 0.7

    # Check parameter overlap
    a_params = {p.name for p in a.parameters}
    b_params = {p.name for p in b.parameters}

    if not a_params and not b_params:
        return 0.3

    if a_params and b_params:
        overlap = len(a_params & b_params) / len(a_params | b_params)
        return 0.5 * overlap

    return 0.0


def _merge_pair(primary: Capability, secondary: Capability) -> Capability:
    """Merge two capabilities representing the same thing.

    Takes the higher-confidence one as primary and enriches it
    with any additional data from secondary.
    """
    # Start with the higher-confidence capability
    if secondary.confidence > primary.confidence:
        primary, secondary = secondary, primary

    # Merge evidence
    merged_evidence = list(primary.evidence)
    for ev in secondary.evidence:
        if ev not in merged_evidence:
            merged_evidence.append(ev)

    # Merge parameters (add any missing from secondary)
    primary_param_names = {p.name for p in primary.parameters}
    merged_params = list(primary.parameters)
    for param in secondary.parameters:
        if param.name not in primary_param_names:
            merged_params.append(param)

    # Merge return schema fields
    merged_returns = primary.returns
    if secondary.returns and secondary.returns.fields:
        primary_field_names = {f.name for f in merged_returns.fields}
        for rf in secondary.returns.fields:
            if rf.name not in primary_field_names:
                merged_returns.fields.append(rf)

    # Boost confidence
    boosted_confidence = min(
        primary.confidence + CROSS_VALIDATION_BOOST,
        MAX_CONFIDENCE,
    )

    # Merge side effects
    merged_effects = list(primary.side_effects)
    for effect in secondary.side_effects:
        if effect not in merged_effects:
            merged_effects.append(effect)

    # Merge prerequisites
    merged_prereqs = list(primary.prerequisites)
    for prereq in secondary.prerequisites:
        if prereq not in merged_prereqs:
            merged_prereqs.append(prereq)

    return Capability(
        id=primary.id,
        name=primary.name,
        description=primary.description or secondary.description,
        source=primary.source,
        parameters=merged_params,
        returns=merged_returns,
        side_effects=merged_effects,
        prerequisites=merged_prereqs,
        confidence=boosted_confidence,
        evidence=merged_evidence,
        idempotent=primary.idempotent,
        domain=primary.domain or secondary.domain,
    )


def cross_validate(
    *capability_lists: list[Capability],
    similarity_threshold: float = 0.7,
) -> MergeResult:
    """Merge capabilities from multiple extractors with cross-validation.

    When multiple extractors independently find the same capability,
    the merged result has higher confidence. When only one extractor
    finds a capability, it keeps its original confidence.

    Args:
        capability_lists: One or more lists of capabilities from different extractors
        similarity_threshold: Minimum similarity to consider two capabilities as matching

    Returns:
        MergeResult with deduplicated, confidence-boosted capabilities
    """
    all_caps: list[Capability] = []
    for cap_list in capability_lists:
        all_caps.extend(cap_list)

    if not all_caps:
        return MergeResult(merged=[])

    # Group by name for quick matching
    by_name: dict[str, list[Capability]] = {}
    for cap in all_caps:
        if cap.name not in by_name:
            by_name[cap.name] = []
        by_name[cap.name].append(cap)

    merged: list[Capability] = []
    duplicates_resolved = 0
    confidence_boosted = 0
    sources_per_cap: dict[str, list[SourceType]] = {}

    # First pass: merge exact name matches
    processed_names: set[str] = set()
    for name, caps in by_name.items():
        if len(caps) == 1:
            merged.append(caps[0])
            sources_per_cap[name] = [caps[0].source.source_type]
        else:
            # Multiple extractors found the same capability
            result = caps[0]
            for other in caps[1:]:
                result = _merge_pair(result, other)
                duplicates_resolved += 1
            confidence_boosted += 1
            merged.append(result)
            sources_per_cap[name] = [c.source.source_type for c in caps]
        processed_names.add(name)

    # Second pass: check for fuzzy matches among remaining
    # (capabilities with different names but same purpose)
    unmatched: list[Capability] = []
    for cap in merged:
        found_match = False
        for other in unmatched:
            sim = _capability_similarity(cap, other)
            if sim >= similarity_threshold:
                # Merge the fuzzy match
                idx = unmatched.index(other)
                unmatched[idx] = _merge_pair(other, cap)
                duplicates_resolved += 1
                confidence_boosted += 1
                found_match = True
                break
        if not found_match:
            unmatched.append(cap)

    # Drop low-confidence capabilities
    low_dropped = 0
    final: list[Capability] = []
    for cap in unmatched:
        if cap.confidence >= MIN_CONFIDENCE_THRESHOLD:
            final.append(cap)
        else:
            low_dropped += 1
            logger.warning(
                f"Dropped low-confidence capability '{cap.name}' "
                f"(confidence={cap.confidence:.2f})"
            )

    logger.info(
        f"Cross-validation: {len(all_caps)} input → {len(final)} merged "
        f"({duplicates_resolved} duplicates, {confidence_boosted} boosted, "
        f"{low_dropped} dropped)"
    )

    return MergeResult(
        merged=final,
        duplicates_resolved=duplicates_resolved,
        confidence_boosted=confidence_boosted,
        low_confidence_dropped=low_dropped,
        sources_per_capability=sources_per_cap,
    )
