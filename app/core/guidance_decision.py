from typing import Any, Dict, List, Optional

from app.core.pathway_knowledge import get_pathway_knowledge


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""

    return (
        value.strip()
        .lower()
        .replace("&", "and")
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
    )


def _normalize_stream(value: Optional[str]) -> str:
    if not value:
        return ""

    value = value.strip().lower()

    replacements = {
        "&": "and",
        "/": " ",
        "-": " ",
        "_": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = " ".join(value.split())

    aliases = {
        "science stream": "science",
        "science": "science",
        "science with mathematics": "science_with_mathematics",
        "science with maths": "science_with_mathematics",
        "science maths": "science_with_mathematics",
        "science math": "science_with_mathematics",
        "pcm": "science_with_mathematics",
        "science with pcm": "science_with_mathematics",
        "science with pcb": "science_with_pcb",
        "science pcb": "science_with_pcb",
        "pcmb": "science_with_pcmb",
        "science with pcmb": "science_with_pcmb",
        "commerce stream": "commerce",
        "commerce": "commerce",
        "arts": "arts_humanities",
        "humanities": "arts_humanities",
        "arts humanities": "arts_humanities",
        "arts and humanities": "arts_humanities",
        "arts humanities stream": "arts_humanities",
        "vocational": "vocational",
    }

    return aliases.get(value, value)


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        return [str(item) for item in value if item]

    return []


# =========================================================
# PATHWAY HELPERS
# =========================================================

def _get_pathway(career_field: Optional[str]) -> Optional[Dict[str, Any]]:
    if not career_field:
        return None

    return get_pathway_knowledge(career_field)


def _same_pathway(
    left: Optional[str],
    right: Optional[str],
) -> bool:
    """
    Compare two career/pathway names using the existing
    pathway knowledge + aliases.

    This avoids creating a second alias system.
    """

    if not left or not right:
        return False

    left_clean = left.strip()
    right_clean = right.strip()

    if left_clean == right_clean:
        return True

    left_pathway = _get_pathway(left_clean)
    right_pathway = _get_pathway(right_clean)

    if left_pathway is None or right_pathway is None:
        return False

    return left_pathway == right_pathway


def _find_interest_match(
    stated_interest: Optional[str],
    top_3: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Find whether the student's stated interest corresponds
    to one of the ML Top-3 pathways.

    Returns the matching Top-3 recommendation or None.
    """

    if not stated_interest:
        return None

    for recommendation in top_3:
        career_field = recommendation.get("career_field")

        if _same_pathway(stated_interest, career_field):
            return recommendation

    return None


# =========================================================
# STREAM COMPATIBILITY
# =========================================================

def _stream_matches_requirement(
    allocated_stream: Optional[str],
    accepted_streams: List[str],
) -> bool:
    """
    Conservative stream compatibility check.

    We intentionally avoid treating generic 'Science' as
    automatically satisfying PCM/PCB requirements.
    """

    if not allocated_stream:
        return False

    allocated = _normalize_stream(allocated_stream)

    if not accepted_streams:
        return True

    normalized_requirements = [
        _normalize_stream(stream)
        for stream in accepted_streams
        if stream
    ]

    for requirement in normalized_requirements:

        # Exact match
        if allocated == requirement:
            return True

        # Generic science pathway
        if requirement == "science":
            if allocated.startswith("science"):
                return True

        # Mathematics-oriented science pathway
        if "mathematics" in requirement or requirement in {
            "science_with_mathematics",
        }:
            if allocated in {
                "science_with_mathematics",
                "science_with_pcmb",
            }:
                return True

        # PCB-oriented science pathway
        if "pcb" in requirement:
            if allocated in {
                "science_with_pcb",
                "science_with_pcmb",
            }:
                return True

        # PCMB-oriented pathway
        if "pcmb" in requirement:
            if allocated == "science_with_pcmb":
                return True

        # Commerce
        if requirement == "commerce":
            if allocated == "commerce":
                return True

        # Arts / Humanities
        if requirement == "arts_humanities":
            if allocated == "arts_humanities":
                return True

        # Vocational
        if requirement == "vocational":
            if allocated == "vocational":
                return True

    return False


def _is_stream_school_eligible(
    allocated_stream: Optional[str],
    eligible_streams: List[str],
) -> Optional[bool]:
    """
    Returns:
        True  -> official school eligibility confirms it
        False -> official eligibility data exists and excludes it
        None  -> eligibility data unavailable
    """

    if not allocated_stream:
        return None

    if not eligible_streams:
        return None

    allocated = _normalize_stream(allocated_stream)

    normalized_eligible = {
        _normalize_stream(stream)
        for stream in eligible_streams
        if stream
    }

    if allocated in normalized_eligible:
        return True

    # Allow equivalent PCM / PCMB representation.
    if allocated == "science_with_mathematics":
        if "science_with_pcmb" in normalized_eligible:
            return True

    if allocated == "science_with_pcb":
        if "science_with_pcmb" in normalized_eligible:
            return True

    return False


# =========================================================
# EDUCATION FEASIBILITY ANALYSIS
# =========================================================

def _analyze_education_feasibility(
    pathway: Optional[Dict[str, Any]],
    education_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    if not pathway:
        return {
            "status": "knowledge_unavailable",
            "allocated_stream": None,
            "stream_compatible": None,
            "school_eligible": None,
            "constraints": [
                "Pathway knowledge is not available for this career field."
            ],
        }

    if not education_state:
        return {
            "status": "unknown",
            "allocated_stream": None,
            "stream_compatible": None,
            "school_eligible": None,
            "constraints": [
                "Educational state is not available yet."
            ],
        }

    allocated_stream = education_state.get("allocated_stream")

    available_streams = _as_list(
        education_state.get("available_streams")
    )

    eligible_streams = _as_list(
        education_state.get("eligible_streams")
    )

    accepted_streams = _as_list(
        pathway.get("accepted_streams")
    )

    result = {
        "status": "unknown",
        "allocated_stream": allocated_stream,
        "available_streams": available_streams,
        "eligible_streams": eligible_streams,
        "accepted_streams": accepted_streams,
        "stream_compatible": None,
        "school_eligible": None,
        "constraints": [],
    }

    # -----------------------------------------------------
    # No official allocation yet
    # -----------------------------------------------------

    if not allocated_stream:
        result["status"] = "pending"

        result["constraints"].append(
            "Final allocated stream is not available yet."
        )

        return result

    # -----------------------------------------------------
    # Stream compatibility
    # -----------------------------------------------------

    stream_compatible = _stream_matches_requirement(
        allocated_stream,
        accepted_streams,
    )

    result["stream_compatible"] = stream_compatible

    if not stream_compatible:
        result["constraints"].append(
            "The student's currently allocated stream does not "
            "match the documented pathway stream requirements."
        )

    # -----------------------------------------------------
    # School eligibility
    # -----------------------------------------------------

    school_eligible = _is_stream_school_eligible(
        allocated_stream,
        eligible_streams,
    )

    result["school_eligible"] = school_eligible

    if school_eligible is False:
        result["constraints"].append(
            "The school's recorded eligibility data does not "
            "list the allocated stream as eligible."
        )

    # -----------------------------------------------------
    # Final status
    # -----------------------------------------------------

    if stream_compatible is False or school_eligible is False:
        result["status"] = "constrained"

    elif stream_compatible is True and (
        school_eligible is True
        or school_eligible is None
    ):
        result["status"] = "feasible"

    else:
        result["status"] = "unknown"

    return result


# =========================================================
# TOP-3 PATHWAY ANALYSIS
# =========================================================

def _analyze_ml_pathway(
    recommendation: Dict[str, Any],
    education_state: Optional[Dict[str, Any]],
    stated_interest: Optional[str],
) -> Dict[str, Any]:

    career_field = recommendation.get("career_field")

    pathway = _get_pathway(career_field)

    education_analysis = _analyze_education_feasibility(
        pathway,
        education_state,
    )

    interest_match = _same_pathway(
        stated_interest,
        career_field,
    )

    result = {
        "rank": recommendation.get("rank"),
        "career_field": career_field,
        "match_confidence_pct": recommendation.get(
            "match_confidence_pct"
        ),
        "interest_alignment": interest_match,
        "education_feasibility": education_analysis,
    }

    if pathway is not None:
        result["pathway_available"] = True
    else:
        result["pathway_available"] = False

    return result


# =========================================================
# CASE DETECTION
# =========================================================

def analyze_guidance_decision(
    top_3: List[Dict[str, Any]],
    stated_interest: Optional[str] = None,
    education_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    # -----------------------------------------------------
    # Normalize basic input
    # -----------------------------------------------------

    if not isinstance(top_3, list):
        top_3 = []

    top_3 = [
        item for item in top_3
        if isinstance(item, dict)
    ]

    clean_interest = (
        stated_interest.strip()
        if isinstance(stated_interest, str)
        and stated_interest.strip()
        else None
    )

    # -----------------------------------------------------
    # Analyze every ML pathway
    # -----------------------------------------------------

    pathway_analysis = [
        _analyze_ml_pathway(
            recommendation,
            education_state,
            clean_interest,
        )
        for recommendation in top_3
    ]

    # -----------------------------------------------------
    # Case 3 detection
    #
    # Stated interest exists but is not one of ML Top 3.
    # This must happen before Case 1/2.
    # -----------------------------------------------------

    interest_match = _find_interest_match(
        clean_interest,
        top_3,
    )

    interest_pathway = (
        _get_pathway(clean_interest)
        if clean_interest
        else None
    )

    interest_outside_top_3 = (
        clean_interest is not None
        and interest_match is None
    )

    if interest_outside_top_3:

        interest_education = _analyze_education_feasibility(
            interest_pathway,
            education_state,
        )

        return {
            "case": "case_3",
            "case_label": "stated_interest_outside_top_3",
            "decision_summary": (
                "The student has expressed interest in a pathway "
                "that is not currently present in the ML Top 3."
            ),
            "ml_top_3_unchanged": True,
            "stated_interest": clean_interest,
            "stated_interest_pathway_available": (
                interest_pathway is not None
            ),
            "stated_interest_education_feasibility": (
                interest_education
            ),
            "interest_matches_ml_top_3": False,
            "top_3_analysis": pathway_analysis,
            "guidance_action": [
                "Keep the ML Top 3 unchanged.",
                "Record and respect the student's stated interest.",
                "Explore the difference between the stated interest "
                "and the assessment-derived directions.",
                "Compare the stated pathway with current educational "
                "constraints when official education data is available.",
                "Suggest low-risk exploration before treating the "
                "stated interest as a confirmed long-term direction.",
            ],
        }

    # -----------------------------------------------------
    # No stated interest:
    # use ML #1 as current primary direction.
    # -----------------------------------------------------

    if not clean_interest:
        active_recommendation = (
            top_3[0]
            if top_3
            else None
        )

    else:
        # Interest is inside Top 3.
        # Use that pathway as the active discussion direction.
        active_recommendation = interest_match

    # -----------------------------------------------------
    # No ML result
    # -----------------------------------------------------

    if not active_recommendation:
        return {
            "case": "insufficient_data",
            "case_label": "insufficient_guidance_data",
            "decision_summary": (
                "There is not enough assessment data to determine "
                "a guidance case."
            ),
            "ml_top_3_unchanged": True,
            "stated_interest": clean_interest,
            "interest_matches_ml_top_3": False,
            "top_3_analysis": pathway_analysis,
            "guidance_action": [
                "Do not generate a strong career conclusion yet.",
                "Wait for a completed assessment result."
            ],
        }

    active_career = active_recommendation.get(
        "career_field"
    )

    active_analysis = next(
        (
            item
            for item in pathway_analysis
            if item.get("career_field") == active_career
        ),
        None,
    )

    education_feasibility = (
        active_analysis.get(
            "education_feasibility"
        )
        if active_analysis
        else None
    )

    # -----------------------------------------------------
    # Case 2:
    # Education / eligibility conflicts with pathway.
    # -----------------------------------------------------

    if education_feasibility:
        if education_feasibility.get("status") == "constrained":

            return {
                "case": "case_2",
                "case_label": "education_or_eligibility_constraint",
                "decision_summary": (
                    "The assessment-derived direction remains "
                    "relevant, but current educational constraints "
                    "create a feasibility conflict."
                ),
                "ml_top_3_unchanged": True,
                "stated_interest": clean_interest,
                "interest_matches_ml_top_3": (
                    interest_match is not None
                ),
                "active_pathway": active_career,
                "active_pathway_rank": active_recommendation.get(
                    "rank"
                ),
                "active_pathway_confidence_pct": (
                    active_recommendation.get(
                        "match_confidence_pct"
                    )
                ),
                "education_feasibility": education_feasibility,
                "top_3_analysis": pathway_analysis,
                "guidance_action": [
                    "Keep the ML Top 3 unchanged.",
                    "Explain the exact educational constraint.",
                    "Identify feasible pathways among the existing "
                    "ML directions where possible.",
                    "Do not automatically override the student's "
                    "allocated stream.",
                    "Do not proactively recommend changing schools "
                    "or streams unless the user asks about that option.",
                ],
            }

    # -----------------------------------------------------
    # Case 1:
    # Pathway aligns and is currently feasible.
    #
    # This includes a student whose stated interest is already
    # one of the Top 3.
    # -----------------------------------------------------

    if education_feasibility:
        status = education_feasibility.get("status")

        if status in {
            "feasible",
            "unknown",
            "pending",
        }:

            return {
                "case": "case_1",
                "case_label": "aligned_or_direct_pathway",
                "decision_summary": (
                    "The current assessment direction is aligned "
                    "with the student's stated interest or is the "
                    "strongest available ML direction, with no "
                    "confirmed educational conflict."
                ),
                "ml_top_3_unchanged": True,
                "stated_interest": clean_interest,
                "interest_matches_ml_top_3": (
                    interest_match is not None
                ),
                "active_pathway": active_career,
                "active_pathway_rank": active_recommendation.get(
                    "rank"
                ),
                "active_pathway_confidence_pct": (
                    active_recommendation.get(
                        "match_confidence_pct"
                    )
                ),
                "education_feasibility": education_feasibility,
                "top_3_analysis": pathway_analysis,
                "guidance_action": [
                    "Keep the ML Top 3 unchanged.",
                    "Explain why the active pathway fits the "
                    "assessment profile.",
                    "Use the education state to describe the "
                    "current direct route.",
                    "Provide concrete exploration and next steps.",
                ],
            }

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    return {
        "case": "insufficient_data",
        "case_label": "guidance_case_not_resolved",
        "decision_summary": (
            "The available guidance data does not yet support "
            "a reliable case classification."
        ),
        "ml_top_3_unchanged": True,
        "stated_interest": clean_interest,
        "interest_matches_ml_top_3": (
            interest_match is not None
        ),
        "top_3_analysis": pathway_analysis,
        "guidance_action": [
            "Do not invent missing educational facts.",
            "Wait for additional authoritative education context "
            "or a future assessment."
        ],
    }