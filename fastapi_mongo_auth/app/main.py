from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes
from app.database.connection import db

app = FastAPI(
    title="FastAPI Mongo Auth",
    description="A robust authentication API using FastAPI and MongoDB. Supports user registration, login, and token management.",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operations with users and tokens.",
        }
    ]
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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
