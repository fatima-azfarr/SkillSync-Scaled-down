"""
SkillSync - Student Profile Endpoint Tests

Tests for:
    POST /students/register
    POST /students/login
    GET /students/{id}
    PUT /students/{id}/profile
    PUT /students/{id}/skills
    PUT /students/{id}/preferences
"""

import pytest


@pytest.mark.asyncio
class TestStudentEndpoints:
    """Tests for student authentication and profile management."""

    async def test_register_and_login_flow(self, async_client):
        """Student can register and then log in successfully."""
        register_payload = {
            "name": "Fatima",
            "email": "fatima@test.edu.pk",
            "password": "password123",
            "skills": ["python"],
            "preferred_domain": "web development",
            "preferred_location": "Lahore",
        }
        res = await async_client.post("/students/register", json=register_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Fatima"
        assert data["email"] == "fatima@test.edu.pk"
        assert data["skills"] == ["python"]
        assert data["preferred_domain"] == "web development"
        assert data["preferred_location"] == "Lahore"
        assert "password_hash" not in data
        student_id = data["id"]

        # Duplicate email should fail with 409
        dup_res = await async_client.post("/students/register", json=register_payload)
        assert dup_res.status_code == 409

        # Login with correct credentials
        login_res = await async_client.post("/students/login", json={
            "email": "fatima@test.edu.pk",
            "password": "password123",
        })
        assert login_res.status_code == 200
        assert login_res.json()["id"] == student_id

        # Login with wrong password
        bad_pw_res = await async_client.post("/students/login", json={
            "email": "fatima@test.edu.pk",
            "password": "wrongpassword",
        })
        assert bad_pw_res.status_code == 401

    async def test_get_student_by_id(self, async_client):
        """GET /students/{id} returns the profile without sensitive fields."""
        reg = await async_client.post("/students/register", json={
            "name": "Ali",
            "email": "ali@test.edu.pk",
            "password": "securepassword1",
            "skills": ["react"],
        })
        student_id = reg.json()["id"]

        res = await async_client.get(f"/students/{student_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Ali"
        assert data["skills"] == ["react"]
        assert "password_hash" not in data

        # Non-existent ID
        not_found_res = await async_client.get("/students/507f1f77bcf86cd799439011")
        assert not_found_res.status_code == 404

        # Invalid ID format
        invalid_res = await async_client.get("/students/invalid-format")
        assert invalid_res.status_code == 404

    async def test_update_student_profile(self, async_client):
        """PUT /students/{id}/profile updates skills, domain, and location."""
        reg = await async_client.post("/students/register", json={
            "name": "Zainab",
            "email": "zainab@test.edu.pk",
            "password": "password123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]

        # Update profile with multiple skills and preferences
        update_payload = {
            "skills": ["python", "web dev", "sql", "react"],
            "preferred_domain": "web development",
            "preferred_location": "Lahore",
        }
        res = await async_client.put(f"/students/{student_id}/profile", json=update_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["skills"] == ["python", "web dev", "sql", "react"]
        assert data["preferred_domain"] == "web development"
        assert data["preferred_location"] == "Lahore"

        # Verify through GET
        fetch_res = await async_client.get(f"/students/{student_id}")
        assert fetch_res.status_code == 200
        fetched = fetch_res.json()
        assert fetched["skills"] == ["python", "web dev", "sql", "react"]
        assert fetched["preferred_domain"] == "web development"
        assert fetched["preferred_location"] == "Lahore"

        # Updating nonexistent student returns 404
        nf_res = await async_client.put("/students/507f1f77bcf86cd799439011/profile", json=update_payload)
        assert nf_res.status_code == 404

    async def test_update_student_skills_and_preferences_endpoints(self, async_client):
        """PUT /students/{id}/skills and PUT /students/{id}/preferences work independently."""
        reg = await async_client.post("/students/register", json={
            "name": "Usman",
            "email": "usman@test.edu.pk",
            "password": "password123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]

        # Update skills only
        skills_res = await async_client.put(f"/students/{student_id}/skills", json={"skills": ["docker", "kubernetes"]})
        assert skills_res.status_code == 200
        assert skills_res.json()["skills"] == ["docker", "kubernetes"]

        # Update preferences only
        pref_res = await async_client.put(f"/students/{student_id}/preferences", json={
            "preferred_domain": "cloud",
            "preferred_location": "Islamabad",
        })
        assert pref_res.status_code == 200
        assert pref_res.json()["preferred_domain"] == "cloud"
        assert pref_res.json()["preferred_location"] == "Islamabad"
        # Skills should remain unchanged
        assert pref_res.json()["skills"] == ["docker", "kubernetes"]

    async def test_update_student_profile_with_education_and_domains(self, async_client):
        """PUT /students/{id}/profile supports university, field_of_study, and domain_interests."""
        reg = await async_client.post("/students/register", json={
            "name": "Asel Nurlanovna",
            "email": "asel@nust.edu.pk",
            "password": "password123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]

        update_payload = {
            "skills": ["python", "react", "typescript"],
            "preferred_domain": "web development",
            "preferred_location": "Islamabad",
            "university": "NUST — National University of Sciences and Technology",
            "field_of_study": "Computer Science",
            "domain_interests": ["Web Development", "AI", "NLP", "Open Source"],
        }
        res = await async_client.put(f"/students/{student_id}/profile", json=update_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["university"] == "NUST — National University of Sciences and Technology"
        assert data["field_of_study"] == "Computer Science"
        assert data["domain_interests"] == ["Web Development", "AI", "NLP", "Open Source"]

        # Test recompute recommendations endpoint
        recompute_res = await async_client.post(f"/students/{student_id}/recompute")
        assert recompute_res.status_code == 200
        assert recompute_res.json()["status"] == "success"

    async def test_get_current_student(self, async_client):
        """GET /students/current returns the active registered student."""
        reg = await async_client.post("/students/register", json={
            "name": "Fatima",
            "email": "fatima@test.edu.pk",
            "password": "password123",
            "skills": ["python", "react"],
        })
        assert reg.status_code == 201

        res = await async_client.get("/students/current")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == reg.json()["id"]
        assert data["name"] == "Fatima"
        assert data["email"] == "fatima@test.edu.pk"


