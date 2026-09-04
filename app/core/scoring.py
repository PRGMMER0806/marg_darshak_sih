import numpy as np
from app.model_schema.question import AptitudeQuestion, RiasecQuestion
import joblib
import json
from pathlib import Path

APT_CATEGORIES = ["numerical", "verbal", "spatial", "logical"]
RIASEC_CATEGORIES = ["R", "I", "A", "S", "E", "C"]
CLUSTER_MAP = {"R": "Realistic", "I": "Investigative", "A": "Artistic", "S": "Social", "E": "Enterprising", "C": "Conventional"}

async def calculate_trait_scores(aptitude_answers: dict, riasec_answers: dict) -> dict:
    apt_correct = {c: 0 for c in APT_CATEGORIES}
    apt_total = {c: 0 for c in APT_CATEGORIES}

    for q in await AptitudeQuestion.find_all().to_list():
        apt_total[q.category] += 1
        if aptitude_answers.get(q.id_code) == q.correct_index:
            apt_correct[q.category] += 1

    apt_scores = {
        f"apt_{c}": round((apt_correct[c] / apt_total[c]) * 100, 2) if apt_total[c] > 0 else 50.0
        for c in APT_CATEGORIES
    }

    riasec_ratings = {c: [] for c in RIASEC_CATEGORIES}
    for q in await RiasecQuestion.find_all().to_list():
        if q.id_code in riasec_answers:
            riasec_ratings[q.category].append(riasec_answers[q.id_code])

    riasec_scores = {}
    for c in RIASEC_CATEGORIES:
        ratings = riasec_ratings[c]
        riasec_scores[f"interest_{c}"] = round(((np.mean(ratings) - 1.0) / 4.0) * 100, 2) if ratings else 50.0

    return {**apt_scores, **riasec_scores}

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "ml_model"

career_model = joblib.load(MODEL_DIR / "career_model.pkl")
kmeans_model = joblib.load(MODEL_DIR / "kmeans_model.pkl")
label_encoder = joblib.load(MODEL_DIR / "label_encoder.pkl")
explainer = joblib.load(MODEL_DIR / "shap_explainer.pkl")
career_metadata = json.load(open(MODEL_DIR / "career_fields_metadata.json"))

FEATURE_COLS = ["apt_numerical", "apt_verbal", "apt_spatial", "apt_logical", "interest_R", "interest_I", "interest_A", "interest_S", "interest_E", "interest_C"]

PERSONA_MAP = {
    0: {"name": "Analytical Innovators", "description": "High scientific inquiry, logical reasoning, and mathematical problem-solving skills."},
    1: {"name": "Technical & Practical Builders", "description": "Hands-on, practical mindset with strong spatial visualization and mechanical interest."},
    2: {"name": "Creative & Visual Designers", "description": "High artistic expression, imagination, and visual-spatial design focus."},
    3: {"name": "Social Guides & Caregivers", "description": "Empathetic, strong verbal communication, focused on helping, teaching, and healthcare."},
    4: {"name": "Enterprise Leaders & Strategists", "description": "Ambitious, persuasive, with strong leadership, communication, and business acumen."},
    5: {"name": "Data & Process Administrators", "description": "Structured, detail-oriented, with high numerical accuracy and preference for clear procedures."},
}

def predict_career(trait_scores: dict) -> dict:
    input_vector = np.array([[trait_scores[col] for col in FEATURE_COLS]])

    cluster_id = int(kmeans_model.predict(input_vector)[0])
    persona = PERSONA_MAP.get(cluster_id, PERSONA_MAP[0])

    probs = career_model.predict_proba(input_vector)[0]
    top_3_indices = np.argsort(probs)[-3:][::-1]

    shap_vals = explainer.shap_values(input_vector)

    recommendations = []
    for rank, idx in enumerate(top_3_indices, start=1):
        career_title = label_encoder.inverse_transform([idx])[0]
        confidence = round(float(probs[idx]) * 100, 2)

        if isinstance(shap_vals, list):
            class_shap = shap_vals[idx][0]
        elif shap_vals.ndim == 3:
            class_shap = shap_vals[0, :, idx]
        else:
            class_shap = shap_vals[0]

        contributions = sorted(
            [{"feature": f, "value": round(float(v), 2), "impact": round(float(w), 4)}
             for f, v, w in zip(FEATURE_COLS, input_vector[0], class_shap)],
            key=lambda x: abs(x["impact"]), reverse=True
        )

        recommendations.append({
            "rank": rank, "career_field": career_title,
            "confidence_pct": confidence, "shap_weights": contributions,
        })

    top = recommendations[0]
    top_factors = [f["feature"] for f in top["shap_weights"] if f["impact"] > 0][:3]
    nlg_summary = (
        f"Your Student Archetype is '{persona['name']}'. "
        f"Your top recommended career path is '{top['career_field']}' with a {top['confidence_pct']}% match. "
        f"Key driving factors: {', '.join(top_factors)}."
    )

    return {
    "persona": persona,
    "recommendations": recommendations,
    "career_field": top["career_field"],
    "score": top["confidence_pct"],
    "nlg_summary": nlg_summary,
}