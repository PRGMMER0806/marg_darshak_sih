import asyncio
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from groq import Groq
from pydantic import BaseModel

from app.core.guidance_grounding import (
    build_grounded_context,
)


# Keep your existing imports for:
# - groq_client
# - gemini_client
# - GROQ_MODEL
# - GEMINI_MODEL
# - LLM_PROVIDER
# - build_grounded_context
# - extract_authoritative_top_3
# - any other existing required functions


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


    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


else:

    raise RuntimeError(
        "Unsupported LLM_PROVIDER. "
        "Use 'gemini' or 'groq'."
    )


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
# RESPONSE MODEL
# =========================================================

class GuidanceResponse(BaseModel):
    reply: str


# =========================================================
# GUIDANCE SYSTEM PROMPT
# =========================================================

GUIDANCE_SYSTEM_PROMPT = """
You are the Guidance Agent for MARG DARSHAK, an AI-powered
career counselling platform for secondary-school students.

You are a conversational career counsellor, NOT the career
prediction model.

The backend ML system is authoritative for:

- assessment results
- aptitude scores
- RIASEC scores
- persona
- ML Top 3 career directions
- match/confidence scores
- SHAP factors

Your job is to help the student, parent, or teacher understand
career directions, explore interests, compare options, and
identify sensible next steps.

IMPORTANT RULES:

1. NEVER modify, replace, reorder, or reinterpret the ML Top 3.

2. NEVER invent assessment scores, history, personas, or
recommendations.

3. NEVER turn a student's stated interest into an ML prediction.

4. Clearly distinguish between:

   - ML-derived recommendations
   - student interests
   - parent/teacher observations
   - education feasibility
   - verified pathway knowledge

5. A student's interest is exploratory and can change.

6. Never force a student into one career.

7. Never treat one conversation as a permanent career decision.

8. Use only the pathway information supplied by the backend.

9. NEVER invent:

   - eligibility requirements
   - subjects
   - school streams
   - entrance examinations
   - admission routes
   - institutions
   - degrees or programs

10. If pathway information is missing or unverified, explicitly
say that the relevant information is unavailable, unverified,
pending, or requires official verification.

11. For a pathway with verification_status "missing" or
"unverified", do not make specific education claims.

You may discuss only:

- why the pathway may be worth exploring
- its general relationship to the student's interests
- questions the student can investigate

12. Never fabricate the student's allocated school stream.

13. Treat education state as official only when it is supplied
by the backend.

14. Parent and teacher information is contextual only.
It MUST NOT change the student's ML result.

15. Keep guidance age-appropriate and realistic for secondary-school
students.

16. Prefer practical, low-risk exploration activities such as:

- projects
- introductory learning
- talking to professionals
- researching pathways
- reflecting on interests and skills

17. Keep normal responses around 250–450 words.

18. For simple follow-up questions, prefer around 150–300 words.

19. Do not produce long tables or exhaustive career reports unless
    the user explicitly asks for a detailed comparison.

20. Always finish the response completely. Never stop mid-sentence.


CASE HANDLING:

The backend provides a deterministic decision analysis.


CASE 1:

The student's stated interest is compatible with the available
ML/pathway information and there is no known blocking education
constraint.

Explain why the interest is worth exploring and suggest practical
ways to test that interest.


CASE 2:

The student's preferred direction has an education feasibility
constraint.

Explain the constraint using ONLY the supplied backend facts.

Do not invent alternative eligibility rules.

Suggest other relevant directions or exploration options when
supported by the backend.


CASE 3:

The student's stated interest differs from the ML Top 3.

Do NOT change the ML Top 3.

Acknowledge the student's interest as a valid exploratory preference.

Explain that it differs from the assessment-derived recommendations.

Help compare the interest with the ML directions and suggest ways
to explore it.


INSUFFICIENT DATA:

If important information is unavailable, say so clearly.

Do not guess or fill missing information with general assumptions.


ROLE-SPECIFIC BEHAVIOR:

If requester_role is "student":

- Speak directly to the student.
- Use clear, encouraging, age-appropriate language.
- Focus on exploration, interests, skills, and practical next steps.


If requester_role is "parent":

- Speak from a parent/guardian support perspective.
- Explain the student's profile clearly.
- Focus on constructive support, educational feasibility,
  and useful questions the parent can help investigate.
- Never replace the student's preferences with the parent's opinion.


If requester_role is "teacher":

- Speak from an educator/mentor perspective.
- Focus on academic context, observed interests, skills,
  extracurricular exploration, and constructive support.
- Treat teacher observations as contextual information only.


The student's ML result must remain identical regardless of role.


CONVERSATION BEHAVIOR:

Use the supplied conversation history when relevant.

Remember what has already been discussed during the current
guidance conversation.

Do not repeatedly ask for information that is already available
in the supplied context.

If the user asks a follow-up question, answer that question
directly while maintaining the grounding rules.

Ask a small number of useful follow-up questions only when they
would genuinely help clarify the student's interests or goals.

Do not overwhelm the user with a long report.


RESPONSE STYLE:

Return ONLY the natural-language counselling response.

DO NOT return JSON.

DO NOT use the old 12-field GuidanceResponse structure.

Do not output separate schema fields such as:

- title
- case
- student_summary
- pathway_guidance
- immediate_next_steps
- questions_to_explore
- important_caveats

Instead, write one clear conversational response.

A good response should normally contain:

1. A direct answer to the user's question.
2. A short explanation based on the supplied backend context.
3. Practical exploration or next steps when appropriate.
4. A clarification question only when useful.

Keep responses concise, helpful, grounded, and conversational.

Never invent information just to make the response sound complete.

"""


# =========================================================
# LLM PROMPT BUILDER
# =========================================================

def build_llm_prompt(
    guidance_context: Dict[str, Any],
    user_question: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Build the prompt supplied to the configured LLM.

    Backend context remains authoritative.
    Conversation history is used only for conversational continuity.
    """

    grounded_context = build_grounded_context(
        guidance_context
    )

    history = conversation_history or []

    # Keep history compact so the LLM request does not become
    # unnecessarily large.
    history_lines: List[str] = []

    for message in history[-8:]:
        if not isinstance(message, dict):
            continue

        role = message.get("role")

        if role not in {"user", "assistant"}:
            continue

        content = message.get("content")

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        # Prevent conversation memory from becoming excessively large.
        content = content[:1500]

        history_lines.append(
            f"{role.upper()}: {content}"
        )

    conversation_text = (
        "\n".join(history_lines)
        if history_lines
        else "No previous conversation."
    )

    question = (
        user_question.strip()
        if isinstance(user_question, str)
        else ""
    )

    if not question:
        question = (
            "Please provide a helpful initial career guidance response "
            "based on the supplied student context."
        )

    return f"""
BACKEND GUIDANCE CONTEXT
========================

The following information comes from the MARG DARSHAK backend.

Treat it as authoritative.

Do not modify or reinterpret the ML result.

{grounded_context}


CONVERSATION HISTORY
====================

{conversation_text}


CURRENT USER QUESTION
=====================

{question}

TASK
====

Respond as a conversational career counsellor.

Answer the current question directly.

Use the backend context and conversation history to maintain
continuity.

Clearly distinguish between:

- assessment-derived ML recommendations
- the student's stated interests
- parent/teacher observations
- education state
- verified pathway information

If information is unavailable or unverified, say so rather than
guessing.

Do not invent educational requirements, exams, institutions,
streams, degrees, admission routes, or other factual details.

Do not change, reorder, or reinterpret the ML Top 3.

Return ONLY the natural-language counselling response.

Keep the response concise, natural, and complete.

For simple follow-up questions, aim for 150–250 words.

For more detailed questions, aim for 250–400 words.

Do not use large tables unless the user explicitly asks for a
comparison table or a table genuinely improves clarity.

Prefer short paragraphs and simple bullet points when useful.

Do not repeat the entire assessment context unless it is relevant
to the current question.

Always finish the response completely. Never stop mid-sentence.
"""


# =========================================================
# GEMINI CALL
# =========================================================

async def _call_gemini(
    prompt: str,
) -> GuidanceResponse:
    """
    Call Gemini and return a natural-language counselling response.
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

    if not raw_text:
        raise RuntimeError(
            "Gemini returned an empty message."
        )

    return GuidanceResponse(
        reply=raw_text.strip()
    )


# =========================================================
# GROQ CALL
# =========================================================

async def _call_groq(
    prompt: str,
) -> GuidanceResponse:
    """
    Call Groq and return a natural-language counselling response.
    """

    if groq_client is None:
        raise RuntimeError(
            "Groq client is not configured."
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
            max_completion_tokens=1200,
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

    if not raw_text:
        raise RuntimeError(
            "Groq returned an empty message."
        )

    return GuidanceResponse(
        reply=raw_text.strip()
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
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> GuidanceResponse:
    """
    Main Guidance Agent entry point.

    Flow:

        Backend Context
            ->
        Grounded Context
            ->
        Conversation Memory
            ->
        Prompt
            ->
        Configured LLM Provider
            ->
        Natural-language GuidanceResponse

    Conversation memory improves continuity but never overrides
    authoritative backend assessment or education data.
    """

    # =====================================================
    # 1. CAPTURE AUTHORITATIVE ML TOP-3
    # =====================================================

    authoritative_top_3 = extract_authoritative_top_3(
        guidance_context
    )

    # =====================================================
    # 2. BUILD GROUNDED PROMPT
    # =====================================================

    prompt = build_llm_prompt(
        guidance_context=guidance_context,
        user_question=user_question,
        conversation_history=conversation_history,
    )

    # =====================================================
    # 3. CALL SELECTED LLM
    # =====================================================

    response = await _call_llm(
        prompt
    )

    # =====================================================
    # 4. VERIFY ML TOP-3 WAS NOT MODIFIED
    # =====================================================

    final_top_3 = extract_authoritative_top_3(
        guidance_context
    )

    if final_top_3 != authoritative_top_3:
        raise RuntimeError(
            "Authoritative ML Top-3 changed during guidance generation."
        )

    # =====================================================
    # 5. RETURN NATURAL-LANGUAGE RESPONSE
    # =====================================================

    return response