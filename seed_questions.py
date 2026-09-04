import json
import asyncio
from pathlib import Path
import os

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

from app.model_schema.question import AptitudeQuestion, RiasecQuestion


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"
QUESTIONS_FILE = BASE_DIR / "questions.json"


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

print("Looking for .env at:")
print(ENV_FILE)

print("Does .env exist?", ENV_FILE.exists())

load_dotenv(dotenv_path=ENV_FILE)

MONGO_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL found:", bool(MONGO_URL))


if not MONGO_URL:
    raise RuntimeError(
        f"DATABASE_URL is not set.\n"
        f"Checked .env at: {ENV_FILE}"
    )


# ---------------------------------------------------------
# SEED
# ---------------------------------------------------------

async def seed():

    client = AsyncIOMotorClient(MONGO_URL)

    db = client.get_default_database()

    await init_beanie(
        database=db,
        document_models=[
            AptitudeQuestion,
            RiasecQuestion,
        ],
    )

    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(
            f"questions.json not found at: {QUESTIONS_FILE}"
        )

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    aptitude_questions = data.get("aptitude_questions", [])
    riasec_questions = data.get("riasec_questions", [])

    print(f"Found {len(aptitude_questions)} aptitude questions")
    print(f"Found {len(riasec_questions)} RIASEC questions")

    aptitude_inserted = 0
    aptitude_skipped = 0

    for q in aptitude_questions:

        existing = await AptitudeQuestion.find_one(
            AptitudeQuestion.id_code == q["id"]
        )

        if existing:
            aptitude_skipped += 1
            continue

        await AptitudeQuestion(
            id_code=q["id"],
            category=q["category"],
            type=q["type"],
            difficulty=q.get("difficulty"),
            prompt=q["prompt"],
            options=q["options"],
            correct_index=q["correct_index"],
        ).insert()

        aptitude_inserted += 1

    riasec_inserted = 0
    riasec_skipped = 0

    for q in riasec_questions:

        existing = await RiasecQuestion.find_one(
            RiasecQuestion.id_code == q["id"]
        )

        if existing:
            riasec_skipped += 1
            continue

        await RiasecQuestion(
            id_code=q["id"],
            category=q["category"],
            type=q["type"],
            statement=q["statement"],
            scale=q.get("scale"),
        ).insert()

        riasec_inserted += 1

    print()
    print("================================")
    print("QUESTION SEEDING COMPLETE")
    print("================================")
    print(f"Aptitude inserted : {aptitude_inserted}")
    print(f"Aptitude skipped  : {aptitude_skipped}")
    print(f"RIASEC inserted   : {riasec_inserted}")
    print(f"RIASEC skipped    : {riasec_skipped}")
    print(f"Database          : {db.name}")
    print("================================")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())