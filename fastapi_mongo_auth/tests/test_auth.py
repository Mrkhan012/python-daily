import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.models.user import UserCreate

# Note: This test script requires 'pytest' and 'httpx' and a running MongoDB instance.
# To run: pytest tests/test_auth.py

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Register
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "mobile": "1234567890",
            "city": "Test City",
            "dob": "2000-01-01",
            "password": "testpassword"
        }
        print("Testing Register...")
        response = await ac.post("/auth/register", json=user_data)
        if response.status_code == 400: # User might already exist from previous run
            print("User already exists, proceeding to login.")
        else:
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == user_data["email"]
            assert "id" in data
            print("Register Success:", data)

        # 2. Login
        login_data = {
            "username": "test@example.com", # OAuth2 form uses username for email
            "password": "testpassword"
        }
        print("Testing Login...")
        response = await ac.post("/auth/login", data=login_data)
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        print("Login Success:", tokens)
        
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 3. Get Me
        print("Testing Get Me...")
        response = await ac.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["email"] == user_data["email"]
        print("Get Me Success:", user_info)

        # 4. Refresh Token
        print("Testing Refresh...")
        response = await ac.post("/auth/refresh", params={"refresh_token": refresh_token}) # passed as query param in my route definition
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        print("Refresh Success:", new_tokens)

if __name__ == "__main__":
    # Simple manual run wrapper if pytest is not available
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_register_and_login())
