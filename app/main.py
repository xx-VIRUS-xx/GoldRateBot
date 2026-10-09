from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()
print(load_dotenv())
from app.routers import whatsapp,rate,inventory

from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
# ENV_PATH = BASE_DIR / ".env"

app=FastAPI()

app.include_router(whatsapp.router)
# app.include_router(rate.router,prefix="/rate")
# app.include_router(inventory.router,prefix="/inventory")