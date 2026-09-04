import json
import pickle
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

MODEL_PATH = 'career_model.pkl'
KMEANS_PATH = 'kmeans_model.pkl'
ENCODER_PATH = 'label_encoder.pkl'
EXPLAINER_PATH = 'shap_explainer.pkl'
METADATA_PATH = 'career_fields_metadata.json'
QUESTIONS_JSON_PATH = 'questions.json'

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

# Load K-Means if available, else fit on metadata
try:
    with open(KMEANS_PATH, 'rb') as f:
        kmeans_model = pickle.load(f)
except Exception:
    from sklearn.cluster import KMeans
    kmeans_model = KMeans(n_clusters=6, random_state=42, n_init=10)

with open(ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)

with open(EXPLAINER_PATH, 'rb') as f:
    explainer = pickle.load(f)

with open(METADATA_PATH, 'r') as f:
    career_metadata = json.load(f)

with open(QUESTIONS_JSON_PATH, 'r') as f:
    questions_data = json.load(f)

FEATURE_COLS = [
    'apt_numerical', 'apt_verbal', 'apt_spatial', 'apt_logical',
    'interest_R', 'interest_I', 'interest_A', 'interest_S', 'interest_E', 'interest_C'
]

PERSONA_MAP = {
    0: {"name": "Analytical Innovators", "description": "High scientific inquiry, logical reasoning, and mathematical problem-solving skills."},
    1: {"name": "Technical & Practical Builders", "description": "Hands-on, practical mindset with strong spatial visualization and mechanical interest."},
    2: {"name": "Creative & Visual Designers", "description": "High artistic expression, imagination, and visual-spatial design focus."},
    3: {"name": "Social Guides & Caregivers", "description": "Empathetic, strong verbal communication, focused on helping, teaching, and healthcare."},
    4: {"name": "Enterprise Leaders & Strategists", "description": "Ambitious, persuasive, with strong leadership, communication, and business acumen."},
    5: {"name": "Data & Process Administrators", "description": "Structured, detail-oriented, with high numerical accuracy and preference for clear procedures."}
}

app = FastAPI(
    title="MARG DARSHAK - AI Career Guidance & Assessment Engine",
    description="API server for SIH1434 AI Career Counselling & Assessment Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentAssessmentInput(BaseModel):
    student_id: str = Field(default="STD_USER")
    class_grade: str = Field(default="Class 10")
    apt_numerical: float = Field(..., ge=0.0, le=100.0)
    apt_verbal: float = Field(..., ge=0.0, le=100.0)
    apt_spatial: float = Field(..., ge=0.0, le=100.0)
    apt_logical: float = Field(..., ge=0.0, le=100.0)
    interest_R: float = Field(..., ge=0.0, le=100.0)
    interest_I: float = Field(..., ge=0.0, le=100.0)
    interest_A: float = Field(..., ge=0.0, le=100.0)
    interest_S: float = Field(..., ge=0.0, le=100.0)
    interest_E: float = Field(..., ge=0.0, le=100.0)
    interest_C: float = Field(..., ge=0.0, le=100.0)

class FullAssessmentSubmission(BaseModel):
    student_id: str = Field(default="STD_1001")
    class_grade: str = Field(default="Class 10")
    aptitude_answers: Dict[str, int] = Field(
        ..., 
        description="Dict mapping Aptitude Question ID to selected option index (0, 1, 2, 3). E.g. {'N1': 0, 'V1': 1}"
    )
    riasec_answers: Dict[str, int] = Field(
        ..., 
        description="Dict mapping RIASEC Question ID to Likert scale rating (1 to 5). E.g. {'R1': 5, 'I1': 4}"
    )

@app.get("/")
def root():
    return {
        "status": "online",
        "platform": "MARG DARSHAK AI Engine",
        "total_supported_career_fields": len(label_encoder.classes_)
    }

@app.get("/api/v1/questions")
def get_official_questions():
    """Returns the official question bank (aptitude multiple choice + RIASEC 1-5 rating items)."""
    return questions_data

@app.post("/api/v1/predict-career")
def predict_career(data: StudentAssessmentInput):
    """Predict top-3 careers + K-Means Student Persona + SHAP feature weights."""
    input_vector = np.array([[
        data.apt_numerical, data.apt_verbal, data.apt_spatial, data.apt_logical,
        data.interest_R, data.interest_I, data.interest_A, data.interest_S,
        data.interest_E, data.interest_C
    ]])

    # 1. K-Means Student Archetype Persona Prediction
    try:
        cluster_id = int(kmeans_model.predict(input_vector)[0])
    except Exception:
        cluster_id = 0
    persona_info = PERSONA_MAP.get(cluster_id, PERSONA_MAP[0])

    # 2. Random Forest Top-3 Career Prediction
    probs = model.predict_proba(input_vector)[0]
    top_3_indices = np.argsort(probs)[-3:][::-1]

    recommendations = []
    shap_vals = explainer.shap_values(input_vector)

    for rank, idx in enumerate(top_3_indices, start=1):
        career_title = label_encoder.inverse_transform([idx])[0]
        match_confidence = round(float(probs[idx]) * 100, 2)

        if isinstance(shap_vals, list):
            class_shap = shap_vals[idx][0]
        elif shap_vals.ndim == 3:
            class_shap = shap_vals[0, :, idx]
        else:
            class_shap = shap_vals[0]

        feature_contributions = []
        for feat_name, feat_val, weight in zip(FEATURE_COLS, input_vector[0], class_shap):
            feature_contributions.append({
                "feature": feat_name,
                "student_score": round(float(feat_val), 2),
                "shap_contribution": round(float(weight), 4)
            })

        feature_contributions.sort(key=lambda x: abs(x["shap_contribution"]), reverse=True)
        meta = career_metadata.get(career_title, {})

        recommendations.append({
            "rank": rank,
            "career_field": career_title,
            "field_id": meta.get("field_id", f"FIELD_{idx+1:02d}"),
            "match_confidence_pct": match_confidence,
            "shap_feature_weights": feature_contributions
        })

    top_career = recommendations[0]["career_field"]
    top_score = recommendations[0]["match_confidence_pct"]
    top_factors = [f["feature"] for f in recommendations[0]["shap_feature_weights"] if f["shap_contribution"] > 0][:3]

    nlg_summary = (
        f"Based on your assessment, your Student Archetype is '{persona_info['name']}'. "
        f"Your top recommended career path is '{top_career}' with a {top_score}% suitability match. "
        f"Key driving factors for this recommendation are your strong performance in {', '.join(top_factors)}. "
        f"Secondary recommended fields include '{recommendations[1]['career_field']}' ({recommendations[1]['match_confidence_pct']}%) "
        f"and '{recommendations[2]['career_field']}' ({recommendations[2]['match_confidence_pct']}%)."
    )

    return {
        "student_id": data.student_id,
        "class_grade": data.class_grade,
        "student_persona": {
            "cluster_id": cluster_id,
            "persona_name": persona_info["name"],
            "description": persona_info["description"]
        },
        "top_recommendation": top_career,
        "nlg_counseling_summary": nlg_summary,
        "recommendations": recommendations
    }

@app.post("/api/v1/submit-assessment")
def submit_assessment(submission: FullAssessmentSubmission):
    """
    Submits student responses from questions.json:
    - aptitude_answers (N1-L6 with option index)
    - riasec_answers (R1-C6 with Likert 1-5 rating)
    Calculates exact trait vectors and generates full AI counseling report.
    """
    # 1. Score Aptitude Questions (Accuracy % per category)
    apt_questions = questions_data['aptitude_questions']
    apt_category_correct = {"numerical": 0, "verbal": 0, "spatial": 0, "logical": 0}
    apt_category_total = {"numerical": 0, "verbal": 0, "spatial": 0, "logical": 0}

    for q in apt_questions:
        q_id = q['id']
        category = q['category']
        correct_idx = q['correct_index']
        apt_category_total[category] += 1

        if q_id in submission.aptitude_answers:
            student_choice = submission.aptitude_answers[q_id]
            if student_choice == correct_idx:
                apt_category_correct[category] += 1

    calculated_apt_scores = {}
    for cat in ["numerical", "verbal", "spatial", "logical"]:
        total = apt_category_total[cat]
        correct = apt_category_correct[cat]
        pct = round((correct / total) * 100.0, 2) if total > 0 else 50.0
        calculated_apt_scores[f"apt_{cat}"] = pct

    # 2. Score RIASEC Questions (Normalized 0-100 score from 1-5 Likert scale)
    riasec_questions = questions_data['riasec_questions']
    riasec_category_ratings = {"R": [], "I": [], "A": [], "S": [], "E": [], "C": []}

    for q in riasec_questions:
        q_id = q['id']
        category = q['category']

        if q_id in submission.riasec_answers:
            rating = submission.riasec_answers[q_id]
            if rating < 1 or rating > 5:
                raise HTTPException(status_code=400, detail=f"Rating for RIASEC question '{q_id}' must be between 1 and 5.")
            riasec_category_ratings[category].append(rating)

    calculated_riasec_scores = {}
    for cat in ["R", "I", "A", "S", "E", "C"]:
        ratings = riasec_category_ratings[cat]
        if ratings:
            avg_rating = np.mean(ratings)
            normalized_score = round(((avg_rating - 1.0) / 4.0) * 100.0, 2)
        else:
            normalized_score = 50.0
        calculated_riasec_scores[f"interest_{cat}"] = normalized_score

    # Combine all 10 trait scores
    full_trait_scores = {**calculated_apt_scores, **calculated_riasec_scores}

    # Pass to prediction pipeline
    assessment_data = StudentAssessmentInput(
        student_id=submission.student_id,
        class_grade=submission.class_grade,
        **full_trait_scores
    )

    result = predict_career(assessment_data)
    result["calculated_feature_scores"] = full_trait_scores
    result["aptitude_score_summary"] = {
        cat: f"{apt_category_correct[cat]}/{apt_category_total[cat]} correct ({calculated_apt_scores[f'apt_{cat}']})"
        for cat in ["numerical", "verbal", "spatial", "logical"]
    }
    return result

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
