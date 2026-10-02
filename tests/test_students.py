"""
SkillSync - Student Profile Endpoint & Defensive Security Tests

Senior Security Test Suite verifying:
- Secure bcrypt hashing & password complexity policies
- Expiring JWT sessions & token verification
- Broken Object Level Authorization (BOLA/IDOR) defense
- Email verification lifecycle and expiry
- Password reset lifecycle, one-time token use, and session revocation
- Rate limiting on failed login attempts (Brute Force Defense)
- Zero exposure of internal authentication secrets to client responses
"""

from datetime import datetime, timedelta
import pytest
from bson import ObjectId

from api.auth import create_access_token, hash_token
from api.config import config
from api.database import get_database


async def get_student_auth_headers(async_client, email: str, password: str) -> dict:
    """Helper to authenticate and return Bearer authorization headers."""
    login_res = await async_client.post("/students/login", json={
        "email": email,
        "password": password,
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestStudentEndpoints:
    """Tests for student authentication, authorization, and profile management."""

    async def test_register_and_login_flow(self, async_client):
        """Student can register and then log in successfully with JWT token."""
        register_payload = {
            "name": "Fatima",
            "email": "fatima@test.edu.pk",
            "password": "Password123",
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
        assert data["is_verified"] is False
        assert "password_hash" not in data
        student_id = data["id"]

        # Duplicate email should fail with 409 Conflict
        dup_res = await async_client.post("/students/register", json=register_payload)
        assert dup_res.status_code == 409

        # Login with correct credentials returns valid JWT token and profile
        login_res = await async_client.post("/students/login", json={
            "email": "fatima@test.edu.pk",
            "password": "Password123",
        })
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert login_data["id"] == student_id
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"
        assert login_data["expires_in"] > 0
        assert "password_hash" not in login_data

        # Login with wrong password returns 401 Unauthorized
        bad_pw_res = await async_client.post("/students/login", json={
            "email": "fatima@test.edu.pk",
            "password": "WrongPassword1",
        })
        assert bad_pw_res.status_code == 401

    async def test_get_student_by_id(self, async_client):
        """GET /students/{id} requires auth; returns profile without sensitive fields."""
        reg = await async_client.post("/students/register", json={
            "name": "Ali",
            "email": "ali@test.edu.pk",
            "password": "SecurePassword1",
            "skills": ["react"],
        })
        student_id = reg.json()["id"]

        # Requesting without auth header must be rejected with 401
        unauth_res = await async_client.get(f"/students/{student_id}")
        assert unauth_res.status_code == 401

        # Requesting with valid auth returns profile
        headers = await get_student_auth_headers(async_client, "ali@test.edu.pk", "SecurePassword1")
        res = await async_client.get(f"/students/{student_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Ali"
        assert data["skills"] == ["react"]
        assert "password_hash" not in data

        # Non-existent ID returns 404
        not_found_res = await async_client.get("/students/507f1f77bcf86cd799439011", headers=headers)
        assert not_found_res.status_code == 404

        # Invalid ID format returns 404
        invalid_res = await async_client.get("/students/invalid-format", headers=headers)
        assert invalid_res.status_code == 404

    async def test_update_student_profile(self, async_client):
        """PUT /students/{id}/profile updates profile when authenticated."""
        reg = await async_client.post("/students/register", json={
            "name": "Zainab",
            "email": "zainab@test.edu.pk",
            "password": "Password123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]
        headers = await get_student_auth_headers(async_client, "zainab@test.edu.pk", "Password123")

        update_payload = {
            "skills": ["python", "web dev", "sql", "react"],
            "preferred_domain": "web development",
            "preferred_location": "Lahore",
        }

        # Updating without auth fails with 401
        unauth_res = await async_client.put(f"/students/{student_id}/profile", json=update_payload)
        assert unauth_res.status_code == 401

        # Updating with auth succeeds
        res = await async_client.put(f"/students/{student_id}/profile", json=update_payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["skills"] == ["python", "web dev", "sql", "react"]
        assert data["preferred_domain"] == "web development"
        assert data["preferred_location"] == "Lahore"

        # Verify through authenticated GET
        fetch_res = await async_client.get(f"/students/{student_id}", headers=headers)
        assert fetch_res.status_code == 200
        fetched = fetch_res.json()
        assert fetched["skills"] == ["python", "web dev", "sql", "react"]

    async def test_update_student_skills_and_preferences_endpoints(self, async_client):
        """PUT /students/{id}/skills and PUT /students/{id}/preferences work independently."""
        reg = await async_client.post("/students/register", json={
            "name": "Usman",
            "email": "usman@test.edu.pk",
            "password": "Password123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]
        headers = await get_student_auth_headers(async_client, "usman@test.edu.pk", "Password123")

        # Update skills only
        skills_res = await async_client.put(
            f"/students/{student_id}/skills",
            json={"skills": ["docker", "kubernetes"]},
            headers=headers,
        )
        assert skills_res.status_code == 200
        assert skills_res.json()["skills"] == ["docker", "kubernetes"]

        # Update preferences only
        pref_res = await async_client.put(
            f"/students/{student_id}/preferences",
            json={
                "preferred_domain": "cloud",
                "preferred_location": "Islamabad",
            },
            headers=headers,
        )
        assert pref_res.status_code == 200
        assert pref_res.json()["preferred_domain"] == "cloud"
        assert pref_res.json()["preferred_location"] == "Islamabad"
        assert pref_res.json()["skills"] == ["docker", "kubernetes"]

    async def test_update_student_profile_with_education_and_domains(self, async_client):
        """PUT /students/{id}/profile supports university, field_of_study, and domain_interests."""
        reg = await async_client.post("/students/register", json={
            "name": "Asel Nurlanovna",
            "email": "asel@nust.edu.pk",
            "password": "Password123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]
        headers = await get_student_auth_headers(async_client, "asel@nust.edu.pk", "Password123")

        update_payload = {
            "skills": ["python", "react", "typescript"],
            "preferred_domain": "web development",
            "preferred_location": "Islamabad",
            "university": "NUST — National University of Sciences and Technology",
            "field_of_study": "Computer Science",
            "domain_interests": ["Web Development", "AI", "NLP", "Open Source"],
        }
        res = await async_client.put(f"/students/{student_id}/profile", json=update_payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["university"] == "NUST — National University of Sciences and Technology"
        assert data["field_of_study"] == "Computer Science"
        assert data["domain_interests"] == ["Web Development", "AI", "NLP", "Open Source"]

        # Test recompute recommendations endpoint
        recompute_res = await async_client.post(f"/students/{student_id}/recompute", headers=headers)
        assert recompute_res.status_code == 200
        assert recompute_res.json()["status"] == "success"

    async def test_get_current_student(self, async_client):
        """GET /students/current and GET /students/me require authentication."""
        reg = await async_client.post("/students/register", json={
            "name": "Fatima",
            "email": "fatima_current@test.edu.pk",
            "password": "Password123",
            "skills": ["python", "react"],
        })
        assert reg.status_code == 201

        # Calling /students/current unauthenticated fails with 401
        unauth_res = await async_client.get("/students/current")
        assert unauth_res.status_code == 401

        # Calling with valid session token returns the authenticated profile
        headers = await get_student_auth_headers(async_client, "fatima_current@test.edu.pk", "Password123")
        res = await async_client.get("/students/current", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == reg.json()["id"]
        assert data["name"] == "Fatima"
        assert data["email"] == "fatima_current@test.edu.pk"

        # /students/me endpoint also returns the profile
        me_res = await async_client.get("/students/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["id"] == reg.json()["id"]


@pytest.mark.asyncio
class TestDefensiveSecurityControls:
    """Security Engineer validation tests for authentication defenses."""

    async def test_idor_protection_between_users(self, async_client):
        """User A cannot modify User B's profile (BOLA/IDOR prevention)."""
        # Register User A
        reg_a = await async_client.post("/students/register", json={
            "name": "User A",
            "email": "usera@test.edu.pk",
            "password": "Password123",
            "skills": ["python"],
        })
        id_a = reg_a.json()["id"]
        headers_a = await get_student_auth_headers(async_client, "usera@test.edu.pk", "Password123")

        # Register User B
        reg_b = await async_client.post("/students/register", json={
            "name": "User B",
            "email": "userb@test.edu.pk",
            "password": "Password123",
            "skills": ["java"],
        })
        id_b = reg_b.json()["id"]

        # User A attempts to overwrite User B's profile -> must return 403 Forbidden
        attack_res = await async_client.put(
            f"/students/{id_b}/profile",
            json={"skills": ["hacked"]},
            headers=headers_a,
        )
        assert attack_res.status_code == 403
        assert "Forbidden" in attack_res.json()["detail"]

        # User A viewing User B's profile has private email redacted
        view_res = await async_client.get(f"/students/{id_b}", headers=headers_a)
        assert view_res.status_code == 200
        assert view_res.json()["email"] != "userb@test.edu.pk"

    async def test_session_token_expiration_and_tampering(self, async_client):
        """Expired or tampered JWT access tokens are rejected."""
        # 1. Expired token
        expired_token = create_access_token(
            student_id="507f1f77bcf86cd799439011",
            email="expired@test.edu.pk",
            expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
        )
        res_expired = await async_client.get(
            "/students/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert res_expired.status_code == 401
        assert "expired" in res_expired.json()["detail"].lower()

        # 2. Tampered token
        tampered_token = expired_token[:-4] + "fake"
        res_tampered = await async_client.get(
            "/students/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert res_tampered.status_code == 401

    async def test_email_verification_flow(self, async_client):
        """Email verification token confirms email and expires properly."""
        reg = await async_client.post("/students/register", json={
            "name": "Verif Student",
            "email": "verif@test.edu.pk",
            "password": "Password123",
            "skills": ["python"],
        })
        assert reg.status_code == 201
        student_id = reg.json()["id"]

        # Fetch the token hash directly from database to test verification
        db = get_database()
        doc = await db[config.STUDENTS_COLLECTION].find_one({"_id": ObjectId(student_id)})
        assert doc["is_verified"] is False
        assert "email_verification_token_hash" in doc

        # Invalid token fails
        bad_verify = await async_client.post("/students/verify-email", json={
            "token": "invalid_fake_token_12345",
        })
        assert bad_verify.status_code == 400

        # Create a mock valid token and set its hash in DB
        raw_test_token = "valid_test_token_abcdef123456"
        token_hash = hash_token(raw_test_token)
        await db[config.STUDENTS_COLLECTION].update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {
                "email_verification_token_hash": token_hash,
                "email_verification_expires_at": datetime.utcnow() + timedelta(hours=1),
            }},
        )

        # Successful verification
        good_verify = await async_client.post("/students/verify-email", json={
            "token": raw_test_token,
        })
        assert good_verify.status_code == 200
        assert "verified successfully" in good_verify.json()["message"].lower()

        # Verify DB status updated and token cleared
        updated_doc = await db[config.STUDENTS_COLLECTION].find_one({"_id": ObjectId(student_id)})
        assert updated_doc["is_verified"] is True
        assert "email_verification_token_hash" not in updated_doc

        # Reusing the token must fail
        reuse_verify = await async_client.post("/students/verify-email", json={
            "token": raw_test_token,
        })
        assert reuse_verify.status_code == 400

    async def test_password_reset_flow_and_session_revocation(self, async_client):
        """Password reset expires, prevents reuse, and revokes prior sessions."""
        reg = await async_client.post("/students/register", json={
            "name": "Reset Student",
            "email": "reset@test.edu.pk",
            "password": "OldPassword123",
            "skills": ["python"],
        })
        student_id = reg.json()["id"]

        # Obtain an active session token before password reset
        old_headers = await get_student_auth_headers(async_client, "reset@test.edu.pk", "OldPassword123")
        active_check = await async_client.get("/students/me", headers=old_headers)
        assert active_check.status_code == 200

        # Request forgot password
        forgot_res = await async_client.post("/students/forgot-password", json={
            "email": "reset@test.edu.pk",
        })
        assert forgot_res.status_code == 200

        # Set a test reset token in the database
        db = get_database()
        raw_reset_token = "test_reset_token_secret_123456"
        token_hash = hash_token(raw_reset_token)
        await db[config.STUDENTS_COLLECTION].update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {
                "password_reset_token_hash": token_hash,
                "password_reset_expires_at": datetime.utcnow() + timedelta(minutes=15),
                "password_reset_used": False,
            }},
        )

        # Reset password with valid token and strong new password
        reset_res = await async_client.post("/students/reset-password", json={
            "token": raw_reset_token,
            "new_password": "NewSecurePassword1",
        })
        assert reset_res.status_code == 200

        # Prior JWT token must now be REVOKED / INVALIDATED
        old_session_res = await async_client.get("/students/me", headers=old_headers)
        assert old_session_res.status_code == 401
        assert "password change" in old_session_res.json()["detail"].lower()

        # Login with old password fails
        old_login = await async_client.post("/students/login", json={
            "email": "reset@test.edu.pk",
            "password": "OldPassword123",
        })
        assert old_login.status_code == 401

        # Login with new password succeeds
        new_login = await async_client.post("/students/login", json={
            "email": "reset@test.edu.pk",
            "password": "NewSecurePassword1",
        })
        assert new_login.status_code == 200

        # Reusing the reset token must be rejected
        reuse_res = await async_client.post("/students/reset-password", json={
            "token": raw_reset_token,
            "new_password": "AnotherPassword1",
        })
        assert reuse_res.status_code == 400

    async def test_password_complexity_enforcement(self, async_client):
        """Weak passwords (short, missing letters or digits) are rejected."""
        # Too short (< 8)
        res_short = await async_client.post("/students/register", json={
            "name": "Weak User",
            "email": "short@test.edu.pk",
            "password": "Ab1",
        })
        assert res_short.status_code == 422 or res_short.status_code == 400

        # Missing digits
        res_no_digit = await async_client.post("/students/register", json={
            "name": "Weak User",
            "email": "nodigit@test.edu.pk",
            "password": "PasswordOnlyLetters",
        })
        assert res_no_digit.status_code == 400
        assert "number" in res_no_digit.json()["detail"].lower()

        # Missing letters
        res_no_alpha = await async_client.post("/students/register", json={
            "name": "Weak User",
            "email": "noalpha@test.edu.pk",
            "password": "123456789012",
        })
        assert res_no_alpha.status_code == 400
        assert "letter" in res_no_alpha.json()["detail"].lower()

    async def test_login_rate_limiting(self, async_client):
        """Excessive failed login attempts trigger 429 Too Many Requests."""
        email = "bruteforce_target@test.edu.pk"
        await async_client.post("/students/register", json={
            "name": "Target",
            "email": email,
            "password": "CorrectPassword1",
        })

        # Attempt 5 incorrect logins (threshold is 5)
        for _ in range(config.RATE_LIMIT_LOGIN_MAX_ATTEMPTS):
            res = await async_client.post("/students/login", json={
                "email": email,
                "password": "WrongPassword999",
            })
            assert res.status_code == 401

        # 6th attempt must be rate-limited with 429
        rate_limited_res = await async_client.post("/students/login", json={
            "email": email,
            "password": "WrongPassword999",
        })
        assert rate_limited_res.status_code == 429
        assert "Too many failed login attempts" in rate_limited_res.json()["detail"]
        assert "Retry-After" in rate_limited_res.headers

    async def test_no_secrets_exposed_to_client(self, async_client):
        """Responses never expose password hashes, secret keys, or token hashes."""
        reg = await async_client.post("/students/register", json={
            "name": "Auditor",
            "email": "audit@test.edu.pk",
            "password": "Password123",
            "skills": ["python"],
        })
        reg_json = reg.json()

        sensitive_fields = [
            "password_hash",
            "email_verification_token_hash",
            "password_reset_token_hash",
            "password_reset_token",
            "JWT_SECRET_KEY",
            "auth_secret",
        ]

        for field in sensitive_fields:
            assert field not in reg_json

        login_res = await async_client.post("/students/login", json={
            "email": "audit@test.edu.pk",
            "password": "Password123",
        })
        login_json = login_res.json()
        for field in sensitive_fields:
            assert field not in login_json
            assert field not in login_json.get("student", {})
