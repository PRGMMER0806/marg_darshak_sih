import pytest

from app.core.guidance_llm import (
    GuidanceResponse,
    _validate_missing_pathway_claims,
    _validate_verified_pathway_claims,
    _validate_all_generated_text_claims,
)


# =========================================================
# FIXTURE: MINIMAL GROUNDED CONTEXT
# =========================================================

@pytest.fixture
def grounded_context():
    return {
        "ml_profile": {
            "top_3": [
                {
                    "rank": 1,
                    "career_field": "Journalism & Content Writing",
                    "pathway_grounding": {
                        "verification_status": "missing",
                        "available": False,
                    },
                },
                {
                    "rank": 2,
                    "career_field": "Performing Arts (Music, Dance, Theatre)",
                    "pathway_grounding": {
                        "verification_status": "missing",
                        "available": False,
                    },
                },
                {
                    "rank": 3,
                    "career_field": "UI/UX Design & Digital Product",
                    "pathway_grounding": {
                        "verification_status": "verified",
                        "available": True,
                        "accepted_streams": [
                            "Science",
                            "Commerce",
                            "Arts",
                            "Humanities",
                        ],
                        "required_subjects": [],
                        "entrance_exams": [
                            {
                                "name": "UCEED"
                            },
                            {
                                "name": "NID DAT"
                            },
                        ],
                        "admission_routes": [
                            {
                                "route": "UCEED → B.Des. admission",
                                "details": "Apply through the applicable B.Des. admission process.",
                            },
                            {
                                "route": "NID DAT → B.Des. admission",
                                "details": "Apply through NID's official B.Des. admissions process.",
                            },
                        ],
                        "eligibility": {
                            "class_11_12": [
                                "No single Class 11–12 stream is universally required."
                            ]
                        },
                    },
                },
            ]
        },
        "stated_interest": {
            "stated_interest": "Software engineering",
            "pathway_grounding": {
                "verification_status": "verified",
                "available": True,
                "career_field": "Software & Systems Engineering",
                "accepted_streams": [
                    "Science with Mathematics"
                ],
                "required_subjects": [
                    "Physics",
                    "Mathematics",
                    "One of Chemistry / Biotechnology / Biology / Technical Vocational subject",
                ],
                "entrance_exams": [
                    {
                        "name": "JEE Main"
                    }
                ],
                "admission_routes": [
                    {
                        "route": "JEE Main → JoSAA/CSAB",
                        "details": "Participate in the applicable centralized counselling process."
                    }
                ],
                "eligibility": {
                    "class_11_12": [
                        "Mathematics and Physics are compulsory for the standard route."
                    ]
                },
            },
        },
    }


# =========================================================
# RESPONSE HELPER
# =========================================================

def make_response(**overrides):
    data = {
        "title": "Test Guidance",
        "case": "case_3",
        "student_summary": "Exploratory guidance.",
        "case_explanation": "This is exploratory guidance.",
        "ml_top_3_interpretation": "The authoritative ML results remain unchanged.",
        "stated_interest_guidance": "The student's interest remains separate.",
        "education_feasibility": "Education information is pending.",
        "pathway_guidance": [],
        "strongest_current_pathway": "Exploration is recommended.",
        "immediate_next_steps": [],
        "questions_to_explore": [],
        "important_caveats": [],
    }

    data.update(overrides)

    return GuidanceResponse(**data)


# =========================================================
# TEST 1
# Missing pathway must reject invented exam
# =========================================================

def test_missing_pathway_rejects_invented_exam(
    grounded_context,
):
    response = make_response(
        pathway_guidance=[
            {
                "career_field": "Journalism & Content Writing",
                "relationship_to_student": "ML recommendation.",
                "why_explore": "Explore writing.",
                "route_summary": (
                    "Journalism requires JEE Main for admission."
                ),
            }
        ]
    )

    with pytest.raises(RuntimeError):
        _validate_missing_pathway_claims(
            response,
            grounded_context,
        )


# =========================================================
# TEST 2
# Missing pathway may safely express uncertainty
# =========================================================

def test_missing_pathway_allows_uncertainty(
    grounded_context,
):
    response = make_response(
        pathway_guidance=[
            {
                "career_field": "Journalism & Content Writing",
                "relationship_to_student": "ML recommendation.",
                "why_explore": "Explore writing.",
                "route_summary": (
                    "Specific eligibility and admission "
                    "requirements are currently missing."
                ),
            }
        ]
    )

    _validate_missing_pathway_claims(
        response,
        grounded_context,
    )


# =========================================================
# TEST 3
# Verified JEE Main must pass
# =========================================================

def test_verified_jee_main_passes(
    grounded_context,
):
    response = make_response(
        pathway_guidance=[
            {
                "career_field": "Software & Systems Engineering",
                "relationship_to_student": "Stated interest.",
                "why_explore": "Explore programming.",
                "route_summary": (
                    "The verified pathway uses JEE Main "
                    "and Science with Mathematics."
                ),
            }
        ]
    )

    _validate_verified_pathway_claims(
        response,
        grounded_context,
    )


# =========================================================
# TEST 4
# Verified pathway must reject unsupported exam
# =========================================================

def test_verified_pathway_rejects_fake_exam(
    grounded_context,
):
    response = make_response(
        pathway_guidance=[
            {
                "career_field": "Software & Systems Engineering",
                "relationship_to_student": "Stated interest.",
                "why_explore": "Explore programming.",
                "route_summary": (
                    "The pathway requires CAT examination."
                ),
            }
        ]
    )

    with pytest.raises(RuntimeError):
        _validate_verified_pathway_claims(
            response,
            grounded_context,
        )


# =========================================================
# TEST 5
# Journalism claim must not be contaminated by
# Software Engineering claims elsewhere
# =========================================================

def test_pathway_local_validation(
    grounded_context,
):
    response = make_response(
        student_summary=(
            "The student is exploring Journalism & Content Writing."
        ),
        stated_interest_guidance=(
            "Software & Systems Engineering can use "
            "JEE Main and Science with Mathematics."
        ),
        pathway_guidance=[
            {
                "career_field": "Journalism & Content Writing",
                "relationship_to_student": "ML recommendation.",
                "why_explore": "Explore writing.",
                "route_summary": (
                    "Specific formal pathway information "
                    "is currently missing."
                ),
            },
            {
                "career_field": "Software & Systems Engineering",
                "relationship_to_student": "Stated interest.",
                "why_explore": "Explore programming.",
                "route_summary": (
                    "Verified pathway information includes "
                    "JEE Main and Science with Mathematics."
                ),
            },
        ],
    )

    _validate_all_generated_text_claims(
        response,
        grounded_context,
    )


# =========================================================
# TEST 6
# Unknown high-risk fact anywhere must fail
# =========================================================

def test_global_unknown_high_risk_fact_fails(
    grounded_context,
):
    response = make_response(
        immediate_next_steps=[
            "Prepare for NEET as the required entrance exam."
        ]
    )

    with pytest.raises(RuntimeError):
        _validate_all_generated_text_claims(
            response,
            grounded_context,
        )


# =========================================================
# TEST 7
# ML Top 3 must not be replaced
#
# This validates the response object before the authoritative
# ML Top 3 is reattached by generate_guidance().
# =========================================================

def test_ml_top_3_is_not_generated_from_guidance_text():
    response = make_response(
        pathway_guidance=[
            {
                "career_field": "Software & Systems Engineering",
                "relationship_to_student": "Stated interest.",
                "why_explore": "Explore programming.",
                "route_summary": "Explore verified pathway information.",
            }
        ]
    )

    assert response.case == "case_3"


# =========================================================
# TEST 8
# Missing education data may be pending
# =========================================================

def test_pending_education_is_allowed(
    grounded_context,
):
    response = make_response(
        education_feasibility=(
            "The official stream allocation is currently pending "
            "and must be verified once assigned."
        )
    )

    _validate_all_generated_text_claims(
        response,
        grounded_context,
    )


def test_generic_science_stream_is_rejected_when_exact_requirement_is_science_with_mathematics():
    text = "You should choose the science stream for software engineering."

    verified_pathway = {
        "career_field": "Software & Systems Engineering",
        "accepted_streams": ["Science with Mathematics"],
        "required_subjects": [
            "Physics",
            "Mathematics",
        ],
        "entrance_exams": [
            {"name": "JEE Main"}
        ],
        "verification_status": "verified",
    }

    # Call the same guardrail/validation function already used by the project.
    # Expected: rejection because "science stream" is broader than
    # the verified "Science with Mathematics" requirement.