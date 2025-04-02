from fastapi import FastAPI
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()

@app.get("/")
async def root():
    return {
        "message": "Hello World",
        "env": os.getenv("POSTGRESQL_APP_USER") # to check if its loading env var properly
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
