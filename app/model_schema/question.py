from beanie import Document
from typing import List, Optional


class AptitudeQuestion(Document):
    id_code: str
    category: str
    type: str
    difficulty: Optional[int] = None
    prompt: str
    options: List[str]
    correct_index: int

    class Settings:
        name = "aptitude_questions"


class RiasecQuestion(Document):
    id_code: str
    category: str
    type: str
    statement: str
    scale: Optional[dict] = None

    class Settings:
        name = "riasec_questions"