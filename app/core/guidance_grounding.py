
from typing import Any, Dict, List, Optional


# =========================================================
# CONSTANTS
# =========================================================

VERIFIED_STATUS = "verified"
UNVERIFIED_STATUS = "unverified"
MISSING_STATUS = "missing"


# =========================================================
# HELPERS
# =========================================================

def _clean_list(
    value: Any,
) -> List[Any]:
    """
    Safely return a list.

    Missing values remain empty.
    No facts are invented.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    return []


def _clean_string(
    value: Any,
) -> Optional[str]:
    """
    Return a cleaned string or None.
    """

    if not isinstance(
        value,
        str,
    ):
        return None

    value = value.strip()

    return value if value else None


# =========================================================
# PATHWAY GROUNDING
# =========================================================

def _ground_pathway(
    pathway: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Convert pathway knowledge into an explicitly grounded form.

    Missing information is never inferred.
    """

    if not pathway:

        return {
            "available": False,
            "verification_status": (
                MISSING_STATUS
            ),
            "career_field": None,
            "academic_year": None,
            "last_verified": None,
            "official_sources": [],
            "accepted_streams": [],
            "required_subjects": [],
            "eligibility": {},
            "programs": [],
            "entrance_exams": [],
            "admission_routes": [],
            "institutions": [],
            "skills_to_build": [],
            "career_outcomes": [],
            "grounding_note": (
                "No structured pathway knowledge is "
                "available for this career field. Do not "
                "state specific eligibility, institution, "
                "examination, or admission facts as "
                "confirmed information."
            ),
        }

    verification_status = _clean_string(
        pathway.get(
            "verification_status"
        )
    )

    if not verification_status:
        verification_status = (
            UNVERIFIED_STATUS
        )

    academic_year = _clean_string(
        pathway.get(
            "academic_year"
        )
    )

    last_verified = _clean_string(
        pathway.get(
            "last_verified"
        )
    )

    official_sources = _clean_list(
        pathway.get(
            "official_sources"
        )
    )

    is_verified = (
        verification_status.lower()
        == VERIFIED_STATUS
        and bool(
            official_sources
        )
    )

    final_status = (
        VERIFIED_STATUS
        if is_verified
        else UNVERIFIED_STATUS
    )

    return {
        "available": True,

        "verification_status": (
            final_status
        ),

        "career_field": (
            pathway.get(
                "career_field"
            )
        ),

        "academic_year": (
            academic_year
        ),

        "last_verified": (
            last_verified
        ),

        "official_sources": (
            official_sources
        ),

        "accepted_streams": _clean_list(
            pathway.get(
                "accepted_streams"
            )
        ),

        "required_subjects": _clean_list(
            pathway.get(
                "required_subjects"
            )
        ),

        "eligibility": pathway.get(
            "eligibility",
            {},
        ),

        "programs": _clean_list(
            pathway.get(
                "programs"
            )
        ),

        "entrance_exams": _clean_list(
            pathway.get(
                "entrance_exams"
            )
        ),

        "admission_routes": _clean_list(
            pathway.get(
                "admission_routes"
            )
        ),

        "institutions": _clean_list(
            pathway.get(
                "institutions"
            )
        ),

        "skills_to_build": _clean_list(
            pathway.get(
                "skills_to_build"
            )
        ),

        "career_outcomes": _clean_list(
            pathway.get(
                "career_outcomes"
            )
        ),

        "grounding_note": (
            "Use these pathway facts only according "
            "to their verification status and supplied scope."
        ),
    }


# =========================================================
# GROUND SINGLE CAREER ENTRY
# =========================================================

def _ground_career_entry(
    career_entry: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Ground one ML Career Path entry.
    """

    career_field = career_entry.get(
        "career_field"
    )

    pathway_knowledge = (
        career_entry.get(
            "pathway_knowledge"
        )
    )

    return {
        "rank": career_entry.get(
            "rank"
        ),

        "career_field": career_field,

        # ML-derived facts
        "ml_match_score": (
            career_entry.get(
                "match_score"
            )
        ),

        "ml_explanation": (
            career_entry.get(
                "why_it_matches"
            )
        ),

        # Career Path data
        "career_path": (
            career_entry.get(
                "career_path"
            )
        ),

        # Structured pathway grounding
        "pathway_grounding": _ground_pathway(
            pathway_knowledge
        ),
    }


# =========================================================
# BUILD GROUNDED CONTEXT
# =========================================================

def build_grounded_context(
    guidance_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the grounded knowledge context passed to Gemini.

    Sources:

    - backend assessment
    - backend ML result
    - backend career path
    - backend pathway knowledge
    - backend student interest
    - backend education state
    - role-scoped parent/teacher context

    No new career facts are generated here.
    """

    ml_profile = guidance_context.get(
        "ml_profile",
        {},
    )

    guidance_data = guidance_context.get(
        "guidance_context",
        {},
    )

    requester = guidance_context.get(
        "requester",
        {},
    )

    if not isinstance(
        ml_profile,
        dict,
    ):
        ml_profile = {}

    if not isinstance(
        guidance_data,
        dict,
    ):
        guidance_data = {}

    if not isinstance(
        requester,
        dict,
    ):
        requester = {}

    # =====================================================
    # 1. ML TOP 3
    # =====================================================

    raw_top_3 = ml_profile.get(
        "top_3",
        [],
    )

    grounded_top_3 = []

    if isinstance(
        raw_top_3,
        list,
    ):

        for career_entry in raw_top_3[:3]:

            if not isinstance(
                career_entry,
                dict,
            ):
                continue

            grounded_top_3.append(
                _ground_career_entry(
                    career_entry
                )
            )

    # =====================================================
    # 2. STATED INTEREST
    # =====================================================

    stated_interest = (
        guidance_data.get(
            "student_interest"
        )
    )

    stated_interest_pathway = (
        guidance_data.get(
            "student_interest_pathway"
        )
    )

    grounded_interest = {
        "stated_interest": (
            stated_interest
        ),
        "pathway_grounding": _ground_pathway(
            stated_interest_pathway
        ),
    }

    # =====================================================
    # 3. INTEREST HISTORY
    # =====================================================

    interest_history = (
        guidance_data.get(
            "interest_history",
            [],
        )
    )

    if not isinstance(
        interest_history,
        list,
    ):
        interest_history = []

    # =====================================================
    # 4. EDUCATION STATE
    # =====================================================

    education_state = (
        guidance_data.get(
            "education_state"
        )
    )

    if not isinstance(
        education_state,
        dict,
    ):
        education_state = None

    # =====================================================
    # 5. DECISION ANALYSIS
    # =====================================================

    decision_analysis = (
        guidance_data.get(
            "decision_analysis"
        )
    )

    if not isinstance(
        decision_analysis,
        dict,
    ):
        decision_analysis = {}

    # =====================================================
    # 6. ROLE-SCOPED HUMAN CONTEXT
    # =====================================================

    parent_context = (
        guidance_data.get(
            "parent_context"
        )
    )

    teacher_context = (
        guidance_data.get(
            "teacher_context"
        )
    )

    if not isinstance(
        parent_context,
        dict,
    ):
        parent_context = None

    if not isinstance(
        teacher_context,
        dict,
    ):
        teacher_context = None

    # =====================================================
    # 7. FINAL GROUNDED DATA
    # =====================================================

    return {

        "grounding_version": "2.0",

        # -------------------------------------------------
        # Requester
        # -------------------------------------------------

        "requester": {
            "role": requester.get(
                "role"
            ),
        },

        # -------------------------------------------------
        # Source policy
        # -------------------------------------------------

        "source_policy": {

            "student_specific_assessment": (
                "backend_assessment_data"
            ),

            "ml_predictions": (
                "backend_ml_result"
            ),

            "career_path_information": (
                "backend_career_path"
            ),

            "eligibility_and_admission": (
                "backend_pathway_knowledge"
            ),

            "student_interest": (
                "backend_student_interest"
            ),

            "education_state": (
                "backend_education_state"
            ),

            "parent_context": (
                "backend_parent_context"
            ),

            "teacher_context": (
                "backend_teacher_context"
            ),
        },

        # -------------------------------------------------
        # ML profile
        # -------------------------------------------------

        "ml_profile": {

            "career_field": (
                ml_profile.get(
                    "career_field"
                )
            ),

            "top_3": grounded_top_3,

            "rule": (
                "The ML profile is authoritative "
                "and must never be modified by the "
                "Guidance Agent."
            ),
        },

        # -------------------------------------------------
        # Student preference
        # -------------------------------------------------

        "stated_interest": (
            grounded_interest
        ),

        "interest_history": (
            interest_history
        ),

        # -------------------------------------------------
        # Human context
        # -------------------------------------------------

        "parent_context": (
            parent_context
        ),

        "teacher_context": (
            teacher_context
        ),

        # -------------------------------------------------
        # Education
        # -------------------------------------------------

        "education_state": (
            education_state
        ),

        # -------------------------------------------------
        # Deterministic decision
        # -------------------------------------------------

        "decision_analysis": (
            decision_analysis
        ),

        # -------------------------------------------------
        # Grounding rules
        # -------------------------------------------------

        "grounding_rules": [

            (
                "Only pathway facts supplied in "
                "pathway_grounding may be treated "
                "as factual pathway knowledge."
            ),

            (
                "A verified pathway may be presented "
                "as verified backend knowledge."
            ),

            (
                "An unverified pathway must not be "
                "presented as confirmed current "
                "eligibility or admission information."
            ),

            (
                "A missing pathway means that specific "
                "pathway facts are unavailable."
            ),

            (
                "Missing education information must be "
                "described as unknown or pending."
            ),

            (
                "Student interests are preferences, "
                "not ML predictions."
            ),

            (
                "Parent and teacher context is guidance "
                "context only."
            ),

            (
                "Parent and teacher context must never "
                "modify assessment or ML results."
            ),

            (
                "Human context must not be presented "
                "as an assessment-derived fact."
            ),
        ],
    }

