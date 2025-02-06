from fastapi import FastAPI
from endpoints.fortune import router as fortune_router

from dotenv import load_dotenv
import os

load_dotenv()
print("USE_MOCK: ", os.getenv("USE_MOCK"))

app = FastAPI(
    title="Fortune API",
    description="Fortune telling API using LLM",
    version="1.0.0"
)

app.include_router(fortune_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Fortune API"}
