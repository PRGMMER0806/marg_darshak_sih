from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from typing import Literal


QuestionType = Literal["aptitude", "riasec"]


class AnswerBase(BaseModel):
    attempt_id: str
    question_id: str
    question_type: QuestionType
    answer_value: int


class AnswerCreate(AnswerBase):
    pass


class Answer(AnswerBase, Document):

    class Settings:
        name = "answers"


class AnswerResponse(AnswerBase):
    id: PydanticObjectId

    class Config:
        json_encoders = {
            PydanticObjectId: str
        }