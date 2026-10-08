from fastapi import FastAPI
from models import Base
from database import engine
from routers import todos, auth

app = FastAPI()

## This adds the db but doesn't work in update
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)
