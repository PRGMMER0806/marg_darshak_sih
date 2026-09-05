from pprint import pprint

from app.core.guidance_decision import analyze_guidance_decision


# =========================================================
# TEST DATA
# =========================================================

TOP_3_SOFTWARE = [
    {
        "rank": 1,
        "career_field": "Software & Systems Engineering",
        "match_confidence_pct": 60.0,
    },
    {
        "rank": 2,
        "career_field": "UI/UX Design & Digital Product",
        "match_confidence_pct": 25.0,
    },
    {
        "rank": 3,
        "career_field": "Architecture & Urban Planning",
        "match_confidence_pct": 15.0,
    },
]


# =========================================================
# CASE 1
# =========================================================

case_1_state = {
    "allocated_stream": "Science with Mathematics",
    "available_streams": [
        "Science with Mathematics",
        "Commerce",
        "Arts/Humanities",
    ],
    "eligible_streams": [
        "Science with Mathematics",
        "Commerce",
        "Arts/Humanities",
    ],
}

case_1 = analyze_guidance_decision(
    top_3=TOP_3_SOFTWARE,
    stated_interest="software engineering",
    education_state=case_1_state,
)

print("\n================ CASE 1 ================\n")
pprint(case_1)


# =========================================================
# CASE 2
# =========================================================

case_2_state = {
    "allocated_stream": "Commerce",
    "available_streams": [
        "Science with Mathematics",
        "Commerce",
        "Arts/Humanities",
    ],
    "eligible_streams": [
        "Science with Mathematics",
        "Commerce",
        "Arts/Humanities",
    ],
}

case_2 = analyze_guidance_decision(
    top_3=TOP_3_SOFTWARE,
    stated_interest="software engineering",
    education_state=case_2_state,
)

print("\n================ CASE 2 ================\n")
pprint(case_2)


# =========================================================
# CASE 3
# =========================================================

case_3_state = {
    "allocated_stream": None,
    "available_streams": [],
    "eligible_streams": [],
}

case_3 = analyze_guidance_decision(
    top_3=[
        {
            "rank": 1,
            "career_field": "Journalism & Content Writing",
            "match_confidence_pct": 34.0,
        },
        {
            "rank": 2,
            "career_field": "Performing Arts (Music, Dance, Theatre)",
            "match_confidence_pct": 19.3,
        },
        {
            "rank": 3,
            "career_field": "UI/UX Design & Digital Product",
            "match_confidence_pct": 17.1,
        },
    ],
    stated_interest="software engineering",
    education_state=case_3_state,
)

print("\n================ CASE 3 ================\n")
pprint(case_3)