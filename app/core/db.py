from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from pathlib import Path
from dotenv import load_dotenv

#connecting with .env file to access database url
load_dotenv(
    dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env"
)


#getting db url 
MONGO_URL = os.getenv("DATABASE_URL")


#1 step initialising of database
async def init_db():
    #settign client and database
    client = AsyncIOMotorClient(MONGO_URL)
    database = client.get_default_database()

    #importing all model files and table models of the respective files in each line
    from app.model_schema.question import AptitudeQuestion,RiasecQuestion  # your Question document
    from app.model_schema.attempt import Attempt
    from app.model_schema.answer import Answer
    from app.model_schema.user import User
    from app.model_schema.parent_context import ParentContext
    from app.model_schema.teacher_context import TeacherContext
    from app.model_schema.message import Message
    from app.model_schema.notification import Notification
    from app.model_schema.flag import FollowUpFlag,Endorsement

    #connecting to db and setting all
    await init_beanie(database=database, document_models=[User,AptitudeQuestion,RiasecQuestion,Attempt,Answer,ParentContext,TeacherContext,Message,Notification,FollowUpFlag,Endorsement])