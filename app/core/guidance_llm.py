
import asyncio
import json
import os
import re
from typing import Any, Dict, List, Literal, Optional, Set

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

from app.core.guidance_grounding import build_grounded_context


# =========================================================
# ENVIRONMENT / LLM PROVIDER
# =========================================================

load_dotenv()

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "gemini",
).strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

gemini_client = None
groq_client = None


if LLM_PROVIDER == "gemini":

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured "
            "while LLM_PROVIDER=gemini."
        )

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


elif LLM_PROVIDER == "groq":

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured "
            "while LLM_PROVIDER=groq."
        )

    from groq import Groq

    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


else:

    raise RuntimeError(
        "Unsupported LLM_PROVIDER. "
        "Use 'gemini' or 'groq'."
    )


# =========================================================
# RESPONSE SCHEMAS
# =========================================================

class PathwayGuidance(BaseModel):
    career_field: str
    relationship_to_student: str
    why_explore: str
    route_summary: str


class GuidanceResponse(BaseModel):
    title: str

    case: Literal[
        "case_1",
        "case_2",
        "case_3",
        "insufficient_data",
    ]

    student_summary: str
    case_explanation: str
    ml_top_3_interpretation: str
    stated_interest_guidance: str
    education_feasibility: str

    pathway_guidance: List[PathwayGuidance]

    strongest_current_pathway: str

    immediate_next_steps: List[str]
    questions_to_explore: List[str]
    important_caveats: List[str]


# =========================================================
# SYSTEM PROMPT
# =========================================================

GUIDANCE_SYSTEM_PROMPT = """
You are the Guidance Agent for MARG DARSHAK, an AI-powered
career counselling platform for secondary-school students.

You are NOT the career prediction model.

The backend ML system is authoritative for:

- assessment results
- aptitude scores
- RIASEC scores
- persona
- ML Top 3 career directions
- match/confidence scores
- SHAP factors

Your responsibility is:

- explain
- compare
- explore
- reason
- guide
- create practical next steps
- discuss educational feasibility only using grounded backend data

CRITICAL RULES:

1. NEVER modify the ML result.

2. NEVER replace the ML Top 3.

3. NEVER invent assessment scores.

4. NEVER invent assessment history.

5. NEVER claim that a student received an ML recommendation
   when the backend did not provide it.

6. NEVER convert a student-stated interest into an ML prediction.

7. A student's interest is mutable and exploratory.

8. Never force the student into one career.

9. Never treat one conversation as a permanent career choice.

10. Never invent eligibility, entrance examinations,
    admission routes, institutions, or subject requirements.

11. Use only supplied grounded backend pathway knowledge
    for specific eligibility/admission facts.

12. Missing or unverified pathway information must be described
    as missing, unavailable, pending, uncertain, or requiring
    official verification.

12A. For pathways whose backend verification_status is "missing"
     or "unverified", DO NOT assert any specific education fact,
     including:

     - stream names
     - subject requirements
     - entrance examinations
     - admission routes
     - university/institution requirements
     - eligibility requirements

     You may only say that this information is unavailable,
     unverified, or requires official verification.

     Do not write statements such as:
     - "Humanities stream is suitable for Journalism."
     - "Commerce stream can be used for Journalism."
     - "Arts stream is required."
     - "Science stream is accepted."

     unless that exact fact exists in verified backend pathway
     knowledge for that pathway.

13. Do not recommend changing schools unless the user explicitly
    asks about changing schools.

14. Parent and teacher context may influence guidance only.
    They MUST NOT alter the ML result.

15. Prefer low-risk exploration activities for secondary-school
    students.

16. Clearly distinguish:

      - assessment-derived ML profile
      - student preference
      - education feasibility
      - verified pathway knowledge

17. When education information is missing, say it is missing.

18. Never fabricate school allocation.

19. The allocated stream is official only when backend education
    state provides it.

20. Keep guidance age-appropriate and realistic.

ROLE-SPECIFIC BEHAVIOR:

The backend provides a "requester_role".

If requester_role is "student":

- Speak directly to the student.
- Focus on exploration, interests, skills, practical next steps,
  and understanding possible pathways.
- Encourage exploration rather than forcing a decision.
- Use age-appropriate language.

If requester_role is "parent":

- Speak from a parent/guardian support perspective.
- Focus on understanding the student's profile, educational
  feasibility, practical support, and questions the parent can
  help with.
- Do not present the parent's opinion as an ML result.
- Do not replace the student's preferences with the parent's
  preferences.
- Parent context is additive only.

If requester_role is "teacher":

- Speak from an educator/mentor perspective.
- Focus on academic evidence, extracurricular context,
  educational feasibility, pathway exploration, and constructive
  support.
- Teacher observations are contextual evidence only.
- Never treat teacher context as an ML prediction input.

The underlying student's assessment profile and ML Top 3 are
identical regardless of requester_role.

Never change the ML result because of the requester role.

ELIGIBILITY TERMINOLOGY RULE:

When discussing streams, subjects, entrance examinations, or eligibility,
use the exact terminology provided by the verified backend pathway knowledge.

Do not broaden, shorten, or paraphrase a verified eligibility term when doing
so could change its meaning.

For example:

- "Science with Mathematics" must not be changed to "science stream".

- Do not say that a student is eligible unless the backend explicitly establishes
  that eligibility.

- If the student's actual allocated/eligible stream is unknown, say that it is
  still pending or unavailable.

The backend pathway knowledge is authoritative for eligibility.

Do not infer missing stream eligibility from general knowledge.

22. Never describe a pathway as having "eligibility across all streams"
    or as being "available to all streams" unless the backend explicitly
    states that exact unrestricted eligibility.

23. If accepted_streams are supplied but institution-specific or
    admission-route-specific conditions also exist, preserve that
    qualification in the response.

24. Never convert "accepted streams" into a claim that every student
    is eligible.

25. Use "accepted streams" only when referring to pathway knowledge.
    Use "eligible" only when the student's own backend education state
    explicitly establishes eligibility.

Respond only according to the supplied JSON schema.
"""


# =========================================================
# AUTHORITATIVE ML TOP-3
# =========================================================

def extract_authoritative_top_3(
    guidance_context: Dict[str, Any],
) -> List[str]:
    """
    Read the ML Top-3 only from the authoritative backend context.
    """

    ml_profile = guidance_context.get(
        "ml_profile",
        {},
    )

    raw_top_3 = ml_profile.get(
        "top_3",
        [],
    )

    if not isinstance(raw_top_3, list):
        return []

    authoritative_top_3: List[str] = []

    for recommendation in raw_top_3[:3]:

        if not isinstance(recommendation, dict):
            continue

        career_field = recommendation.get(
            "career_field"
        )

        if isinstance(career_field, str):

            career_field = career_field.strip()

            if career_field:
                authoritative_top_3.append(
                    career_field
                )

    return authoritative_top_3


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_llm_prompt(
    guidance_context: Dict[str, Any],
    user_question: Optional[str] = None,
) -> str:
    """
    Build a structured prompt using the grounded backend context.
    """

    grounded_context = build_grounded_context(
        guidance_context
    )

    authoritative_top_3 = extract_authoritative_top_3(
        guidance_context
    )

    prompt_payload = {
        "authoritative_ml_top_3": authoritative_top_3,

        "requester_role": guidance_context.get(
            "requester",
            {},
        ).get(
            "role"
        ),

        "grounded_context": grounded_context,

        "user_question": user_question,
    }

    serialized_context = json.dumps(
        prompt_payload,
        indent=2,
        default=str,
    )

    return f"""
Generate guidance using ONLY the backend context below.

IMPORTANT:

The field "authoritative_ml_top_3" contains the exact ML Top-3.

It is immutable.

Do not replace, reorder, reinterpret, or modify those career
directions or their scores.

Do not treat a student-stated interest as an ML prediction.

Grounding rules:

- verified pathway facts may be presented as verified backend data
- missing pathway facts must not be invented
- unverified facts must not be presented as confirmed
- missing education information must be described as pending/unknown
- parent/teacher context cannot modify ML predictions

Eligibility terminology rules:

- When discussing streams, subjects, entrance examinations, or eligibility,
  use the terminology supplied by the verified backend pathway knowledge.

- Do not broaden, shorten, or paraphrase an eligibility requirement if doing
  so could change its meaning.

- Do not describe a pathway as "fully accessible across all academic streams"
  when the backend states that institution-specific requirements may apply.

- Do not state that a student is eligible unless the backend explicitly
  establishes that eligibility.

- When the student's allocated stream or actual eligibility is unavailable,
  describe it as pending or unknown.

Example:

If the backend says accepted streams are "Science", "Commerce", "Arts",
and "Humanities", prefer:

"can be explored from Science, Commerce, Arts, or Humanities, although
specific institutions and admission routes may have additional eligibility
requirements."

USER QUESTION:

{user_question or "Provide general guidance based on the current profile."}

BACKEND CONTEXT:

{serialized_context}
"""


# =========================================================
# NORMALIZATION
# =========================================================

def _normalize_text(value: Any) -> str:

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    )


# =========================================================
# GROUNDED PATHWAY INDEX
# =========================================================

def _build_grounded_pathway_index(
    grounded_context: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Build:

        normalized career field
            ->
        pathway grounding information
    """

    index: Dict[str, Dict[str, Any]] = {}

    ml_profile = grounded_context.get(
        "ml_profile",
        {},
    )

    top_3 = ml_profile.get(
        "top_3",
        [],
    )

    if isinstance(top_3, list):

        for item in top_3:

            if not isinstance(item, dict):
                continue

            career_field = item.get(
                "career_field"
            )

            pathway_grounding = item.get(
                "pathway_grounding"
            )

            if (
                isinstance(career_field, str)
                and isinstance(
                    pathway_grounding,
                    dict,
                )
            ):

                index[
                    _normalize_text(career_field)
                ] = pathway_grounding

    stated_interest = grounded_context.get(
        "stated_interest",
        {},
    )

    if isinstance(stated_interest, dict):

        interest_name = stated_interest.get(
            "stated_interest"
        )

        pathway_grounding = stated_interest.get(
            "pathway_grounding"
        )

        if isinstance(
            pathway_grounding,
            dict,
        ):

            grounded_name = (
                pathway_grounding.get(
                    "career_field"
                )
                or interest_name
            )

            if isinstance(
                grounded_name,
                str,
            ):

                index[
                    _normalize_text(
                        grounded_name
                    )
                ] = pathway_grounding

    return index


# =========================================================
# HIGH-RISK FACT TERMS
# =========================================================

HIGH_RISK_FACT_TERMS = {
    "jee main",
    "uceed",
    "nid dat",
    "josaa",
    "csab",
    "physics",
    "mathematics",
    "maths",
    "science with mathematics",
    "science stream",
    "commerce stream",
    "arts stream",
    "humanities stream",
}


# =========================================================
# UNCERTAINTY MARKERS
# =========================================================

UNCERTAINTY_MARKERS = {
    "not confirmed",
    "not currently available",
    "currently unavailable",
    "missing",
    "unavailable",
    "unknown",
    "not verified",
    "unverified",
    "cannot confirm",
    "can't confirm",
    "do not have verified",
    "don't have verified",
    "does not have verified",
    "not confirmed in the backend",
    "not available in the backend",
    "not documented",
    "not supplied",
    "has not been supplied",
    "not provided",
    "not recorded",
    "pending",
    "requires verification",
    "should be verified",
    "check official",
    "verify official",
    "official verification required",
    "requires official verification",
    "not enough information",
    "insufficient information",
    "no verified",
    "without verified",
}

# =========================================================
# ASSERTION DETECTION
# =========================================================


def _term_is_present_as_assertion(
    text: str,
    term: str,
) -> bool:
    """
    Returns True only when a factual term is actually asserted.

    Returns False when the specific occurrence of the term is:
    - explicitly negated
    - marked as unknown/unverified
    - framed as hypothetical
    - described as unavailable
    - followed/preceded by wording that clearly removes the claim

    Important:
    Uncertainty elsewhere in the same sentence must NOT cancel
    an unrelated factual assertion.

    Example:

        "Humanities subjects may be useful. No verified pathway
        details are available."

    The "No verified pathway details..." statement does NOT make
    the earlier "Humanities subjects may be useful" claim safe.
    """

    normalized_text = _normalize_text(text)
    normalized_term = _normalize_text(term)

    if (
        not normalized_text
        or not normalized_term
        or normalized_term not in normalized_text
    ):
        return False

    # ---------------------------------------------------------
    # Find every occurrence of the risky term.
    # ---------------------------------------------------------

    occurrence_pattern = re.compile(
        rf"\b{re.escape(normalized_term)}\b",
        flags=re.IGNORECASE,
    )

    matches = list(
        occurrence_pattern.finditer(
            normalized_text
        )
    )

    if not matches:
        return False

    # ---------------------------------------------------------
    # Examine each occurrence independently.
    # ---------------------------------------------------------

    for match in matches:

        start = match.start()
        end = match.end()

        # Look at a limited local window around THIS occurrence.
        # This prevents a later unrelated uncertainty statement
        # from cancelling an earlier factual claim.
        local_start = max(
            0,
            start - 100,
        )

        local_end = min(
            len(normalized_text),
            end + 140,
        )

        local_text = normalized_text[
            local_start:local_end
        ]

        # -----------------------------------------------------
        # 1. Explicit negation / unavailable wording
        # -----------------------------------------------------

        negative_patterns = [

            # humanities stream is not required
            rf"\b{re.escape(normalized_term)}\b"
            rf"\s+(?:is|are|was|were)\s+"
            rf"(?:not|never)\b",

            # humanities stream is unavailable
            rf"\b{re.escape(normalized_term)}\b"
            rf"\s+(?:is|are|was|were)\s+"
            rf"(?:unavailable|unknown|uncertain)\b",

            # not humanities stream
            rf"\b(?:not|never)\s+"
            rf"{re.escape(normalized_term)}\b",

            # no humanities stream requirement
            rf"\b(?:no|without)\s+"
            rf"(?:verified\s+)?"
            rf"{re.escape(normalized_term)}\b",

            # cannot confirm humanities stream
            rf"\b(?:cannot|can't|can\s+not|"
            rf"do\s+not|don't|does\s+not|doesn't|"
            rf"unable\s+to)\b"
            rf".{{0,80}}?"
            rf"\b{re.escape(normalized_term)}\b",

            # whether humanities stream is required
            rf"\b(?:whether|if)\b"
            rf".{{0,80}}?"
            rf"\b{re.escape(normalized_term)}\b"
            rf".{{0,80}}?"
            rf"\b(?:required|eligible|available|accepted)\b",

            # check/verify humanities stream
            rf"\b(?:check|verify|confirm|review)\b"
            rf".{{0,80}}?"
            rf"\b{re.escape(normalized_term)}\b",
        ]

        explicitly_non_assertive = False

        for pattern in negative_patterns:

            if re.search(
                pattern,
                local_text,
                flags=re.IGNORECASE,
            ):
                explicitly_non_assertive = True
                break

        if explicitly_non_assertive:
            continue

        # -----------------------------------------------------
        # 2. Uncertainty immediately associated with the term
        # -----------------------------------------------------

        local_uncertainty_patterns = [

            rf"\b(?:unverified|unknown|uncertain|"
            rf"unavailable|missing|pending|not\s+confirmed|"
            rf"not\s+verified|not\s+provided|not\s+recorded)\b"
            rf".{{0,60}}?"
            rf"\b{re.escape(normalized_term)}\b",

            rf"\b{re.escape(normalized_term)}\b"
            rf".{{0,60}}?"
            rf"\b(?:unverified|unknown|uncertain|"
            rf"unavailable|missing|pending|not\s+confirmed|"
            rf"not\s+verified|not\s+provided|not\s+recorded)\b",
        ]

        locally_uncertain = False

        for pattern in local_uncertainty_patterns:

            if re.search(
                pattern,
                local_text,
                flags=re.IGNORECASE,
            ):
                locally_uncertain = True
                break

        if locally_uncertain:
            continue

        # -----------------------------------------------------
        # 3. Hypothetical/example wording
        # -----------------------------------------------------

        hypothetical_patterns = [

            rf"\b(?:if|whether|suppose|assuming)\b"
            rf".{{0,80}}?"
            rf"\b{re.escape(normalized_term)}\b",

            rf"\b(?:for\s+example|for\s+instance)\b"
            rf".{{0,80}}?"
            rf"\b{re.escape(normalized_term)}\b",

            rf"\b(?:such\s+as|e\.g\.)\b"
            rf".{{0,80}}?"
            rf"\b{re.escape(normalized_term)}\b",
        ]

        hypothetical = False

        for pattern in hypothetical_patterns:

            if re.search(
                pattern,
                local_text,
                flags=re.IGNORECASE,
            ):
                hypothetical = True
                break

        if hypothetical:
            continue

        # -----------------------------------------------------
        # 4. Explicit verification
        # -----------------------------------------------------

        verification_markers = [
            "verified backend",
            "verified backend knowledge",
            "backend knowledge confirms",
            "backend records confirm",
            "official source confirms",
        ]

        for marker in verification_markers:

            if marker in local_text:
                return True

        # -----------------------------------------------------
        # 5. This occurrence is an actual assertion.
        # -----------------------------------------------------

        return True

    # All occurrences were non-assertive.
    return False


# =========================================================
# SENTENCE EXTRACTION
# =========================================================

def _split_into_claim_units(
    text: str,
) -> List[str]:
    """
    Split text into small claim units.

    This is important because pathway-specific validation must
    not allow facts belonging to Software Engineering to be
    incorrectly attributed to Journalism.
    """

    if not isinstance(
        text,
        str,
    ):
        return []

    units = re.split(
        r"(?<=[.!?])\s+|[\n]+",
        text,
    )

    return [
        unit.strip()
        for unit in units
        if unit.strip()
    ]


# =========================================================
# EXAM CLAIM DETECTION
# =========================================================

EXAM_CLAIM_PATTERNS = [

    re.compile(
        r"\b(?:requires?|required|needs?|mandatory)"
        r"\s*(?:the\s+)?"
        r"([A-Za-z][A-Za-z0-9&.\-]*(?:\s+[A-Za-z][A-Za-z0-9&.\-]*){0,4})"
        r"\s*(?:entrance\s+)?"
        r"(?:exam|examination)\b",
        flags=re.IGNORECASE,
    ),

    re.compile(
        r"\b(?:prepare\s+for|appear\s+for|take|qualify\s+in)"
        r"\s*(?:the\s+)?"
        r"([A-Za-z][A-Za-z0-9&.\-]*(?:\s+[A-Za-z][A-Za-z0-9&.\-]*){0,4})"
        r"\s*(?:as\s+)?"
        r"(?:the\s+)?"
        r"(?:required\s+|mandatory\s+|qualifying\s+)?"
        r"(?:entrance\s+)?"
        r"(?:exam|examination)\b",
        flags=re.IGNORECASE,
    ),
]


EXAM_TRAILING_STOPWORDS = {
    "as",
    "the",
    "a",
    "an",
    "required",
    "mandatory",
    "qualifying",
    "entrance",
    "exam",
    "examination",
}


def _clean_exam_candidate(
    candidate: str,
) -> str:
    """
    Clean an extracted exam candidate.
    """

    candidate = candidate.strip(
        " .,;:()[]{}"
    )

    words = candidate.split()

    cleaned_words: List[str] = []

    for word in words:

        normalized_word = word.strip(
            ".,;:()[]{}"
        ).lower()

        if normalized_word in EXAM_TRAILING_STOPWORDS:
            break

        cleaned_words.append(
            word.strip(
                ".,;:()[]{}"
            )
        )

    return " ".join(
        cleaned_words
    ).strip()


def _extract_exam_claims(
    text: str,
) -> List[str]:
    """
    Extract likely entrance-exam names from explicit factual
    examination claims.
    """

    if not isinstance(
        text,
        str,
    ):
        return []

    claims: List[str] = []

    for pattern in EXAM_CLAIM_PATTERNS:

        for match in pattern.finditer(text):

            candidate = _clean_exam_candidate(
                match.group(1)
            )

            if candidate:
                claims.append(
                    candidate
                )

    # ---------------------------------------------------------
    # Explicit special case:
    #
    # "Prepare for NEET as the required entrance exam."
    #
    # ---------------------------------------------------------

    contextual_pattern = re.compile(
        r"\b(?:prepare\s+for|appear\s+for|take|qualify\s+in)"
        r"\s*(?:the\s+)?"
        r"([A-Za-z][A-Za-z0-9&.\-]{1,30})"
        r"\s*"
        r"(?:as\s+)?"
        r"(?:the\s+)?"
        r"(?:required\s+|mandatory\s+|qualifying\s+)?"
        r"(?:entrance\s+)?"
        r"exam(?:ination)?\b",
        flags=re.IGNORECASE,
    )

    for match in contextual_pattern.finditer(text):

        candidate = _clean_exam_candidate(
            match.group(1)
        )

        if candidate:
            claims.append(
                candidate
            )

    # ---------------------------------------------------------
    # Preserve order while removing duplicates.
    # ---------------------------------------------------------

    unique_claims: List[str] = []
    seen: Set[str] = set()

    for claim in claims:

        normalized = _normalize_text(
            claim
        )

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        unique_claims.append(
            claim
        )

    return unique_claims


def _collect_verified_exam_names(
    grounded_context: Dict[str, Any],
) -> Set[str]:
    """
    Collect ONLY explicit entrance-exam names from verified
    backend pathway knowledge.
    """

    verified_exam_names: Set[str] = set()

    pathway_index = _build_grounded_pathway_index(
        grounded_context
    )

    for pathway in pathway_index.values():

        if not isinstance(
            pathway,
            dict,
        ):
            continue

        if pathway.get(
            "verification_status"
        ) != "verified":
            continue

        entrance_exams = pathway.get(
            "entrance_exams",
            [],
        )

        if not isinstance(
            entrance_exams,
            list,
        ):
            continue

        for exam in entrance_exams:

            if not isinstance(
                exam,
                dict,
            ):
                continue

            name = exam.get(
                "name"
            )

            if (
                isinstance(name, str)
                and name.strip()
            ):

                verified_exam_names.add(
                    _normalize_text(name)
                )

    return verified_exam_names


def _exam_claim_is_verified(
    exam_name: str,
    verified_exam_names: Set[str],
) -> bool:
    """
    Exact normalized match against explicitly verified exams.
    """

    normalized_exam = _normalize_text(
        exam_name
    )

    if not normalized_exam:
        return False

    return normalized_exam in verified_exam_names


def _validate_exam_claims(
    text: str,
    verified_exam_names: Set[str],
    context_label: str,
) -> None:
    """
    Reject explicit exam claims not present in verified backend
    entrance-exam data.
    """

    exam_claims = _extract_exam_claims(
        text
    )

    for exam_name in exam_claims:

        if not _exam_claim_is_verified(
            exam_name,
            verified_exam_names,
        ):

            raise RuntimeError(
                (
                    "LLM used an unverified entrance-exam claim "
                    f"('{exam_name}') {context_label}."
                )
            )


# =========================================================
# VERIFIED FACT COLLECTION
# =========================================================

def _collect_verified_terms(
    grounded_context: Dict[str, Any],
) -> Set[str]:
    """
    Collect specific factual terms explicitly represented
    by verified backend pathway knowledge.
    """

    verified_terms: Set[str] = set()

    pathway_index = _build_grounded_pathway_index(
        grounded_context
    )

    for pathway in pathway_index.values():

        if not isinstance(
            pathway,
            dict,
        ):
            continue

        if pathway.get(
            "verification_status"
        ) != "verified":
            continue

        # -----------------------------------------------------
        # Accepted streams
        # -----------------------------------------------------

        for stream in pathway.get(
            "accepted_streams",
            [],
        ) or []:

            if isinstance(
                stream,
                str,
            ):

                verified_terms.add(
                    _normalize_text(stream)
                )

        # -----------------------------------------------------
        # Required subjects
        # -----------------------------------------------------

        for subject in pathway.get(
            "required_subjects",
            [],
        ) or []:

            if isinstance(
                subject,
                str,
            ):

                normalized_subject = _normalize_text(
                    subject
                )

                verified_terms.add(
                    normalized_subject
                )

        # -----------------------------------------------------
        # Entrance exams
        # -----------------------------------------------------

        for exam in pathway.get(
            "entrance_exams",
            [],
        ) or []:

            if not isinstance(
                exam,
                dict,
            ):
                continue

            name = exam.get(
                "name"
            )

            if isinstance(
                name,
                str,
            ):

                verified_terms.add(
                    _normalize_text(name)
                )

        # -----------------------------------------------------
        # Admission routes
        # -----------------------------------------------------

        for route in pathway.get(
            "admission_routes",
            [],
        ) or []:

            if not isinstance(
                route,
                dict,
            ):
                continue

            route_name = route.get(
                "route"
            )

            route_details = route.get(
                "details"
            )

            if isinstance(
                route_name,
                str,
            ):

                normalized_route = _normalize_text(
                    route_name
                )

                verified_terms.add(
                    normalized_route
                )

                parts = re.split(
                    r"(?:→|->|/|,|;|\||:|\(|\)|\[|\])",
                    normalized_route,
                )

                for part in parts:

                    part = _normalize_text(
                        part
                    )

                    if part:
                        verified_terms.add(
                            part
                        )

            if isinstance(
                route_details,
                str,
            ):

                normalized_details = _normalize_text(
                    route_details
                )

                verified_terms.add(
                    normalized_details
                )

        # -----------------------------------------------------
        # Eligibility
        # -----------------------------------------------------

        eligibility = pathway.get(
            "eligibility",
            {},
        )

        if isinstance(
            eligibility,
            dict,
        ):

            for value in eligibility.values():

                if isinstance(
                    value,
                    list,
                ):

                    for item in value:

                        if not isinstance(
                            item,
                            str,
                        ):
                            continue

                        normalized_item = _normalize_text(
                            item
                        )

                        verified_terms.add(
                            normalized_item
                        )

                        for fact_term in HIGH_RISK_FACT_TERMS:

                            if fact_term in normalized_item:

                                verified_terms.add(
                                    fact_term
                                )

                elif isinstance(
                    value,
                    str,
                ):

                    normalized_value = _normalize_text(
                        value
                    )

                    verified_terms.add(
                        normalized_value
                    )

                    for fact_term in HIGH_RISK_FACT_TERMS:

                        if fact_term in normalized_value:

                            verified_terms.add(
                                fact_term
                            )

        # -----------------------------------------------------
        # Institutions / programmes
        # -----------------------------------------------------

        for institution in pathway.get(
            "institutions",
            [],
        ) or []:

            if not isinstance(
                institution,
                dict,
            ):
                continue

            name = institution.get(
                "name"
            )

            if isinstance(
                name,
                str,
            ):

                verified_terms.add(
                    _normalize_text(name)
                )

            program = institution.get(
                "program"
            )

            if isinstance(
                program,
                str,
            ):

                verified_terms.add(
                    _normalize_text(program)
                )

    return verified_terms


# =========================================================
# PATHWAY NAME VALIDATION
# =========================================================

def _validate_pathway_names(
    response: GuidanceResponse,
    grounded_context: Dict[str, Any],
) -> None:
    """
    Prevent the LLM from inventing unsupported pathway names.
    """

    pathway_index = _build_grounded_pathway_index(
        grounded_context
    )

    known_pathways = set(
        pathway_index.keys()
    )

    for pathway in response.pathway_guidance:

        normalized_name = _normalize_text(
            pathway.career_field
        )

        if normalized_name not in known_pathways:

            raise RuntimeError(
                (
                    "LLM introduced an unsupported pathway "
                    f"'{pathway.career_field}'."
                )
            )


# =========================================================
# MISSING / UNVERIFIED PATHWAY VALIDATION
# =========================================================

def _validate_missing_pathway_claims(
    response: GuidanceResponse,
    grounded_context: Dict[str, Any],
) -> None:
    """
    Validate pathway entries whose backend knowledge is missing
    or unverified.
    """

    pathway_index = _build_grounded_pathway_index(
        grounded_context
    )

    verified_terms = _collect_verified_terms(
        grounded_context
    )

    verified_exam_names = _collect_verified_exam_names(
        grounded_context
    )

    for pathway in response.pathway_guidance:

        career_field = pathway.career_field

        grounding = pathway_index.get(
            _normalize_text(career_field)
        )

        if not grounding:
            continue

        status = grounding.get(
            "verification_status"
        )

        if status not in {
            "missing",
            "unverified",
        }:
            continue

        pathway_text = " ".join(
            [
                pathway.relationship_to_student,
                pathway.why_explore,
                pathway.route_summary,
            ]
        )

        normalized_pathway_text = _normalize_text(
            pathway_text
        )

        # -----------------------------------------------------
        # Specific high-risk factual claims
        # -----------------------------------------------------

        for term in HIGH_RISK_FACT_TERMS:

            if not _term_is_present_as_assertion(
                normalized_pathway_text,
                term,
            ):
                continue

            raise RuntimeError(
                (
                    "LLM used an unsupported factual claim "
                    f"('{term}') for '{career_field}', which has "
                    f"verification_status='{status}'. "
                    "Missing/unverified pathways must not contain "
                    "specific education facts."
                )
            )

        # -----------------------------------------------------
        # Unknown entrance exam claims
        # -----------------------------------------------------

        _validate_exam_claims(
            pathway_text,
            verified_exam_names,
            (
                f"for '{career_field}', which has "
                f"verification_status='{status}'"
            ),
        )

        # -----------------------------------------------------
        # Generic eligibility/admission language
        # -----------------------------------------------------

        risky_general_terms = {
            "eligibility",
            "admission",
            "entrance",
            "institution",
            "university",
            "college",
        }

        mentions_general_terms = any(
            term in normalized_pathway_text
            for term in risky_general_terms
        )

        if mentions_general_terms:

            has_uncertainty = any(
                marker in normalized_pathway_text
                for marker in UNCERTAINTY_MARKERS
            )

            # Explicit uncertainty/absence wording is acceptable.
           #
            # Examples:
            # "eligibility information is unavailable"
            # "I cannot confirm admission requirements"
            # "no verified admission information is available"
            #
            # The LLM is not asserting an eligibility fact in these cases.
            if has_uncertainty:
                continue

            raise RuntimeError(
                (
                    "LLM discussed eligibility/admission "
                    f"information for '{career_field}' without "
                    "providing the required uncertainty marker."
                )
            )


# =========================================================
# VERIFIED PATHWAY VALIDATION
# =========================================================

def _validate_verified_pathway_claims(
    response: GuidanceResponse,
    grounded_context: Dict[str, Any],
) -> None:
    """
    Ensure specific high-risk facts used inside each verified
    pathway actually exist in verified backend knowledge.
    """

    pathway_index = _build_grounded_pathway_index(
        grounded_context
    )

    verified_terms = _collect_verified_terms(
        grounded_context
    )

    verified_exam_names = _collect_verified_exam_names(
        grounded_context
    )

    for pathway in response.pathway_guidance:

        career_field = pathway.career_field

        grounding = pathway_index.get(
            _normalize_text(career_field)
        )

        if not grounding:
            continue

        if grounding.get(
            "verification_status"
        ) != "verified":
            continue

        pathway_text = " ".join(
            [
                pathway.relationship_to_student,
                pathway.why_explore,
                pathway.route_summary,
            ]
        )

        # -----------------------------------------------------
        # Specific high-risk factual terms
        # -----------------------------------------------------

        for term in HIGH_RISK_FACT_TERMS:

            if not _term_is_present_as_assertion(
                pathway_text,
                term,
            ):
                continue

            # Mathematics / Maths equivalence
            if term in {
                "mathematics",
                "maths",
            }:

                if verified_terms.intersection(
                    {
                        "mathematics",
                        "maths",
                    }
                ):
                    continue

            if term not in verified_terms:

                raise RuntimeError(
                    (
                        "LLM used an education/admission fact "
                        f"('{term}') for '{career_field}' that is "
                        "not explicitly represented in the verified "
                        "backend pathway knowledge."
                    )
                )

        # -----------------------------------------------------
        # Exact verified entrance exams
        # -----------------------------------------------------

        _validate_exam_claims(
            pathway_text,
            verified_exam_names,
            f"for verified pathway '{career_field}'",
        )

# =========================================================
# VERIFIED PATHWAY VALIDATION
# =========================================================

def _validate_all_generated_text_claims(
    response: GuidanceResponse,
    grounded_context: Dict[str, Any],
) -> None:
    """
    Validate factual claims across all generated fields.

    Pathway-specific validation is local to claim units that
    actually mention the relevant pathway.
    """

    generated_sections: List[str] = [
        response.student_summary,
        response.case_explanation,
        response.ml_top_3_interpretation,
        response.stated_interest_guidance,
        response.education_feasibility,
        response.strongest_current_pathway,
        *response.immediate_next_steps,
        *response.questions_to_explore,
        *response.important_caveats,
    ]

    for pathway in response.pathway_guidance:
        generated_sections.extend(
            [
                pathway.relationship_to_student,
                pathway.why_explore,
                pathway.route_summary,
            ]
        )

    combined_text = "\n".join(
        section
        for section in generated_sections
        if isinstance(section, str)
        and section.strip()
    )

    pathway_index = _build_grounded_pathway_index(
        grounded_context
    )

    verified_terms = _collect_verified_terms(
        grounded_context
    )

    verified_exam_names = _collect_verified_exam_names(
        grounded_context
    )

    # ---------------------------------------------------------
    # Pathway-local validation across every generated section.
    # ---------------------------------------------------------

    claim_units = _split_into_claim_units(
        combined_text
    )

    for career_field, pathway_data in pathway_index.items():

        status = pathway_data.get(
            "verification_status"
        )

        if status not in {
            "missing",
            "unverified",
        }:
            continue

        for claim in claim_units:

            normalized_claim = _normalize_text(
                claim
            )

            if career_field not in normalized_claim:
                continue

            # -------------------------------------------------
            # Specific high-risk claims
            # -------------------------------------------------

            for term in HIGH_RISK_FACT_TERMS:

                # Ignore mentions that are clearly uncertainty,
                # negation, hypothetical examples, or absence
                # statements.
                if not _term_is_present_as_assertion(
                    claim,
                    term,
                ):
                    continue

                # -------------------------------------------------
                # Mathematics / Maths equivalence
                # -------------------------------------------------

                if term in {
                    "mathematics",
                    "maths",
                }:
                    if verified_terms.intersection(
                        {
                            "mathematics",
                            "maths",
                        }
                    ):
                        continue

                # -------------------------------------------------
                # Exact verified term
                # -------------------------------------------------

                if term in verified_terms:
                    continue

                # -------------------------------------------------
                # Do not allow an unverified high-risk fact.
                # -------------------------------------------------

                raise RuntimeError(
                    (
                        "LLM used a high-risk factual term "
                        f"('{term}') for '{career_field}' "
                        "that is not explicitly represented "
                        "in verified backend pathway knowledge."
                    )
                )

            # -------------------------------------------------
            # Unknown entrance exams
            # -------------------------------------------------

            _validate_exam_claims(
                claim,
                verified_exam_names,
                (
                    f"for '{career_field}', which has "
                    f"verification_status='{status}'"
                ),
            )

            # -------------------------------------------------
            # Generic eligibility/admission claims
            # -------------------------------------------------

            generic_terms = {
                "eligibility",
                "admission",
                "entrance",
                "institution",
                "university",
                "college",
            }

            mentions_generic_term = any(
                term in normalized_claim
                for term in generic_terms
            )

            if mentions_generic_term:

                has_uncertainty = any(
                    marker in normalized_claim
                    for marker in UNCERTAINTY_MARKERS
                )

                if has_uncertainty:
                    continue

                raise RuntimeError(
                    (
                        "LLM discussed eligibility/admission "
                        f"information for '{career_field}' "
                        "without providing the required "
                        "uncertainty marker."
                    )
                )

    # ---------------------------------------------------------
    # Global specific-fact protection.
    # ---------------------------------------------------------

    for claim in claim_units:

        # -----------------------------------------------------
        # Known high-risk factual terms
        # -----------------------------------------------------

        for term in HIGH_RISK_FACT_TERMS:

            # Ignore uncertainty, negation, hypothetical,
            # or explicit absence statements.
            if not _term_is_present_as_assertion(
                claim,
                term,
            ):
                continue

            # -------------------------------------------------
            # Mathematics / Maths equivalence
            # -------------------------------------------------

            if term in {
                "mathematics",
                "maths",
            }:

                if verified_terms.intersection(
                    {
                        "mathematics",
                        "maths",
                    }
                ):
                    continue

            # -------------------------------------------------
            # Exact verified term
            # -------------------------------------------------

            if term in verified_terms:
                continue

            # -------------------------------------------------
            # Reject unsupported factual terms.
            # -------------------------------------------------

            raise RuntimeError(
                (
                    "LLM used a high-risk factual term "
                    f"('{term}') that is not explicitly "
                    "represented in verified backend pathway "
                    "knowledge."
                )
            )

        # -----------------------------------------------------
        # Unknown / unverified entrance exams
        # -----------------------------------------------------

        _validate_exam_claims(
            claim,
            verified_exam_names,
            "in generated guidance",
        )

# =========================================================
# RESPONSE VALIDATION
# =========================================================

def validate_guidance_response(
    response: GuidanceResponse,
    guidance_context: Dict[str, Any],
) -> GuidanceResponse:
    """
    Execute the complete guardrail pipeline.
    """

    grounded_context = build_grounded_context(
        guidance_context
    )

    # ---------------------------------------------------------
    # 1. Pathway identities
    # ---------------------------------------------------------

    _validate_pathway_names(
        response=response,
        grounded_context=grounded_context,
    )

    # ---------------------------------------------------------
    # 2. Missing / unverified pathway facts
    # ---------------------------------------------------------

    _validate_missing_pathway_claims(
        response=response,
        grounded_context=grounded_context,
    )

    # ---------------------------------------------------------
    # 3. Verified pathway facts
    # ---------------------------------------------------------

    _validate_verified_pathway_claims(
        response=response,
        grounded_context=grounded_context,
    )

    # ---------------------------------------------------------
    # 4. ALL generated text
    # ---------------------------------------------------------

    _validate_all_generated_text_claims(
        response=response,
        grounded_context=grounded_context,
    )

    return response


# =========================================================
# LLM RESPONSE PARSER
# =========================================================

async def _parse_guidance_response(
    raw_text: Optional[str],
    provider_name: str,
) -> GuidanceResponse:
    """
    Parse and validate structured LLM JSON output.
    """

    if not raw_text:

        raise RuntimeError(
            f"{provider_name} returned no textual guidance response."
        )

    try:

        parsed = json.loads(
            raw_text
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            (
                f"{provider_name} returned invalid JSON for the "
                f"GuidanceResponse schema: {exc}"
            )
        ) from exc

    try:

        return GuidanceResponse.model_validate(
            parsed
        )

    except Exception as exc:

        raise RuntimeError(
            (
                f"{provider_name} response did not match the "
                f"GuidanceResponse schema: {exc}"
            )
        ) from exc


# =========================================================
# GEMINI CALL
# =========================================================

async def _call_gemini(
    prompt: str,
) -> GuidanceResponse:
    """
    Call Gemini and request structured JSON output.
    """

    if gemini_client is None:

        raise RuntimeError(
            "Gemini client is not configured."
        )

    def _sync_call():

        return gemini_client.models.generate_content(
            model=GEMINI_MODEL,

            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                GUIDANCE_SYSTEM_PROMPT
                                + "\n\n"
                                + prompt
                            )
                        }
                    ],
                }
            ],

            config={
                "response_mime_type": "application/json",
                "response_schema": GuidanceResponse,
            },
        )

    try:

        response = await asyncio.to_thread(
            _sync_call
        )

    except Exception as exc:

        raise RuntimeError(
            f"Gemini request failed: {exc}"
        ) from exc

    if response is None:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    raw_text = getattr(
        response,
        "text",
        None,
    )

    return await _parse_guidance_response(
        raw_text=raw_text,
        provider_name="Gemini",
    )


# =========================================================
# GROQ CALL
# =========================================================

async def _call_groq(
    prompt: str,
) -> GuidanceResponse:
    """
    Call Groq and request JSON Schema structured output.

    The currently configured model is expected to support
    JSON Schema output.
    """

    if groq_client is None:

        raise RuntimeError(
            "Groq client is not configured."
        )

    response_schema = (
        GuidanceResponse.model_json_schema()
    )

    def _sync_call():

        return groq_client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": GUIDANCE_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            response_format={
                "type": "json_schema",

                "json_schema": {
                    "name": "guidance_response",
                    "schema": response_schema,
                },
            },
        )

    try:

        response = await asyncio.to_thread(
            _sync_call
        )

    except Exception as exc:

        raise RuntimeError(
            f"Groq request failed: {exc}"
        ) from exc

    if response is None:

        raise RuntimeError(
            "Groq returned an empty response."
        )

    choices = getattr(
        response,
        "choices",
        None,
    )

    if not choices:

        raise RuntimeError(
            "Groq returned no choices."
        )

    message = getattr(
        choices[0],
        "message",
        None,
    )

    if message is None:

        raise RuntimeError(
            "Groq returned no message."
        )

    raw_text = getattr(
        message,
        "content",
        None,
    )

    return await _parse_guidance_response(
        raw_text=raw_text,
        provider_name="Groq",
    )


# =========================================================
# LLM PROVIDER ROUTER
# =========================================================

async def _call_llm(
    prompt: str,
) -> GuidanceResponse:
    """
    Route the request to the configured LLM provider.
    """

    if LLM_PROVIDER == "gemini":

        return await _call_gemini(
            prompt
        )

    if LLM_PROVIDER == "groq":

        return await _call_groq(
            prompt
        )

    raise RuntimeError(
        f"Unsupported LLM provider: {LLM_PROVIDER}"
    )


# =========================================================
# PUBLIC GUIDANCE GENERATOR
# =========================================================

async def generate_guidance(
    guidance_context: Dict[str, Any],
    user_question: Optional[str] = None,
) -> GuidanceResponse:
    """
    Main Guidance Agent entry point.

    Flow:

        Backend Context
            ->
        Grounded Prompt
            ->
        Configured LLM Provider
            ->
        Pydantic Response Validation
            ->
        Guidance Guardrails
            ->
        Final Response

    The LLM does not modify the authoritative ML result.
    """

    # ---------------------------------------------------------
    # Capture authoritative ML Top-3 BEFORE the LLM call.
    # ---------------------------------------------------------

    authoritative_top_3 = (
        extract_authoritative_top_3(
            guidance_context
        )
    )

    # ---------------------------------------------------------
    # Build grounded prompt.
    # ---------------------------------------------------------

    prompt = build_llm_prompt(
        guidance_context=guidance_context,
        user_question=user_question,
    )

    # ---------------------------------------------------------
    # Call the selected provider.
    #
    # LLM_PROVIDER=gemini -> Gemini
    # LLM_PROVIDER=groq   -> Groq
    # ---------------------------------------------------------

    response = await _call_llm(
        prompt
    )

    # ---------------------------------------------------------
    # Run complete guardrail pipeline.
    # ---------------------------------------------------------

    response = validate_guidance_response(
        response=response,
        guidance_context=guidance_context,
    )

    # ---------------------------------------------------------
    # Final immutable ML check.
    #
    # Re-read the authoritative backend context and make sure
    # the ML Top-3 is exactly the same as before the LLM call.
    # ---------------------------------------------------------

    final_top_3 = extract_authoritative_top_3(
        guidance_context
    )

    if final_top_3 != authoritative_top_3:

        raise RuntimeError(
            "Authoritative ML Top-3 changed during guidance generation."
        )

    # ---------------------------------------------------------
    # Final return.
    # ---------------------------------------------------------

    return response

