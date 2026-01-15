from fastapi import FastAPI
from app.routes import auth_routes
from app.database.connection import db

app = FastAPI(title="FastAPI Mongo Auth")

@app.on_event("startup")
async def startup_db_client():
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.disconnect()

app.include_router(auth_routes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Mongo Auth API"}
