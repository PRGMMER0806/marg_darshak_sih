from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.db import init_db
from app.routers import auth,aptitude,dashboard,career,student,parent,teacher,message,notification
from fastapi.middleware.cors import CORSMiddleware


#before exec, setting database and connecting all tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # runs once when the app starts up
    yield  # app runs here
    # any cleanup code would go after yield, on shutdown



#include all routers
app = FastAPI(title="1st stage proto", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(aptitude.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(career.router)
app.include_router(student.router)
app.include_router(parent.router)
app.include_router(teacher.router)
app.include_router(message.router)
app.include_router(notification.router)

#status check
@app.get("/")
def root():
    return {"status": "API is running"}