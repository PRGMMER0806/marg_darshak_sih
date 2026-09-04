from app.model_schema.attempt import Attempt
from app.model_schema.user import User

async def get_weekly_trend(user_id: str) -> dict:
    attempts = await Attempt.find(Attempt.user_id == user_id).sort("+taken_at").to_list()
    weekly = {}
    for a in attempts:
        week = a.taken_at.strftime("%Y-W%U")
        weekly.setdefault(week, []).append(a.score or 0)
    return {week: round(sum(scores) / len(scores), 2) for week, scores in weekly.items()}

async def get_peer_average(school_id: str, class_name: str) -> float | None:
    students = await User.find(User.role == "student", User.school_id == school_id, User.class_name == class_name).to_list()
    scores = []
    for s in students:
        latest = await Attempt.find(Attempt.user_id == str(s.id)).sort("-taken_at").first_or_none()
        if latest and latest.score is not None:
            scores.append(latest.score)
    return round(sum(scores) / len(scores), 2) if scores else None