from datetime import datetime, timezone
import logging
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from api.auth import (
    create_access_token,
    generate_reset_token,
    generate_verification_token,
    get_client_ip,
    get_current_student,
    hash_password,
    hash_token,
    login_rate_limiter,
    password_reset_rate_limiter,
    require_student_ownership,
    validate_password_complexity,
    verification_rate_limiter,
    verify_password,
)
from api.config import config
from api.database import get_database
from api.models import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    ResendVerificationRequest,
    StudentLogin,
    StudentLoginResponse,
    StudentPreferencesUpdate,
    StudentProfileUpdate,
    StudentRegister,
    StudentResponse,
    StudentSkillsUpdate,
    VerifyEmailRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Students"])


def _student_to_response(doc: dict, public_view: bool = False) -> StudentResponse:
    """
    Map a MongoDB student document to the public-facing response model.
    
    Security controls:
    - Strictly excludes password_hash, token hashes, and internal timestamps.
    - When public_view=True (viewing another user's profile), redacts email to prevent harvesting.
    """
    first_name = doc.get("first_name")
    last_name = doc.get("last_name")
    if not first_name and doc.get("name"):
        parts = doc["name"].strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    email = "redacted@skillsync.internal" if public_view else doc.get("email", "")

    return StudentResponse(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        first_name=first_name,
        last_name=last_name,
        email=email,
        skills=doc.get("skills", []),
        preferred_domain=doc.get("preferred_domain"),
        preferred_location=doc.get("preferred_location"),
        university=doc.get("university"),
        field_of_study=doc.get("field_of_study"),
        domain_interests=doc.get("domain_interests", []),
        is_verified=doc.get("is_verified", False),
        created_at=doc.get("created_at") or datetime.utcnow(),
    )


def _object_id_or_404(student_id: str) -> ObjectId:
    try:
        return ObjectId(student_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid student ID format",
        )


@router.post(
    "/register",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student",
    description="Create a new student account with password validation and email verification initialization.",
)
async def register_student(payload: StudentRegister):
    # Enforce password security policy
    validate_password_complexity(payload.password)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    email_clean = payload.email.lower().strip()
    existing = await collection.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    first_name = payload.first_name
    last_name = payload.last_name
    if not first_name and payload.name:
        parts = payload.name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    # Generate one-time email verification token (store hash, never raw token in DB)
    raw_verify_token, verify_token_hash, verify_expires_at = generate_verification_token()

    student_doc = {
        "name": payload.name.strip(),
        "first_name": first_name.strip() if first_name else None,
        "last_name": last_name.strip() if last_name else None,
        "email": email_clean,
        "password_hash": hash_password(payload.password),
        "is_verified": False,
        "email_verification_token_hash": verify_token_hash,
        "email_verification_expires_at": verify_expires_at,
        "skills": payload.skills,
        "preferred_domain": payload.preferred_domain,
        "preferred_location": payload.preferred_location,
        "university": payload.university,
        "field_of_study": payload.field_of_study,
        "domain_interests": payload.domain_interests,
        "created_at": datetime.utcnow(),
    }

    try:
        result = await collection.insert_one(student_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    student_doc["_id"] = result.inserted_id

    # Defensive logging: log verification token dispatch for dev/audit
    logger.info(f"[AUTH] Account created for {email_clean}. Verification token: {raw_verify_token}")

    return _student_to_response(student_doc)


@router.post(
    "/login",
    response_model=StudentLoginResponse,
    summary="Log in a student",
    description="Authenticate credentials with rate-limiting and return a secure expiring JWT access token.",
)
async def login_student(request: Request, payload: StudentLogin):
    client_ip = get_client_ip(request)
    email_clean = payload.email.lower().strip()
    rate_key = f"login:{client_ip}:{email_clean}"

    # Rate limiting protection against credential stuffing and brute force
    is_limited, retry_after = login_rate_limiter.is_rate_limited(
        rate_key,
        config.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
        config.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({"email": email_clean})
    if not doc or not verify_password(payload.password, doc.get("password_hash", "")):
        login_rate_limiter.record_attempt(rate_key)
        # Identical error prevents user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reset rate limiting attempts on successful login
    login_rate_limiter.reset(rate_key)

    # Issue cryptographically signed expiring access token
    access_token = create_access_token(
        student_id=str(doc["_id"]),
        email=doc["email"],
    )

    student_resp = _student_to_response(doc)
    expires_in_seconds = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return StudentLoginResponse(
        id=student_resp.id,
        name=student_resp.name,
        email=student_resp.email,
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        is_verified=student_resp.is_verified,
        student=student_resp,
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify student email",
    description="Validate the one-time verification token and mark the student's email as verified.",
)
async def verify_email(payload: VerifyEmailRequest):
    token_hash = hash_token(payload.token.strip())

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({"email_verification_token_hash": token_hash})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email verification token.",
        )

    expires_at = doc.get("email_verification_expires_at")
    if not expires_at or expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification token has expired. Please request a new verification email.",
        )

    # Update account status and unset one-time token fields
    await collection.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "is_verified": True,
                "verified_at": datetime.utcnow(),
            },
            "$unset": {
                "email_verification_token_hash": "",
                "email_verification_expires_at": "",
            },
        },
    )

    return MessageResponse(
        status="success",
        message="Email verified successfully. Your account is now fully verified.",
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Generate and dispatch a fresh email verification link with rate limiting.",
)
async def resend_verification(request: Request, payload: ResendVerificationRequest):
    client_ip = get_client_ip(request)
    email_clean = payload.email.lower().strip()
    rate_key = f"verify_resend:{client_ip}:{email_clean}"

    is_limited, retry_after = verification_rate_limiter.is_rate_limited(
        rate_key,
        config.RATE_LIMIT_VERIFY_MAX_ATTEMPTS,
        config.RATE_LIMIT_VERIFY_WINDOW_SECONDS,
    )
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many verification requests. Please wait {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    verification_rate_limiter.record_attempt(rate_key)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({"email": email_clean})
    if doc and not doc.get("is_verified", False):
        raw_verify_token, verify_token_hash, verify_expires_at = generate_verification_token()
        await collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "email_verification_token_hash": verify_token_hash,
                    "email_verification_expires_at": verify_expires_at,
                }
            },
        )
        logger.info(f"[AUTH] Resent verification token for {email_clean}: {raw_verify_token}")

    # Constant response to prevent email harvesting
    return MessageResponse(
        status="success",
        message="If an unverified account with this email exists, a verification link has been sent.",
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Initiate a password reset flow. Issues an expiring single-use reset token.",
)
async def forgot_password(request: Request, payload: ForgotPasswordRequest):
    client_ip = get_client_ip(request)
    email_clean = payload.email.lower().strip()
    rate_key = f"reset_req:{client_ip}:{email_clean}"

    is_limited, retry_after = password_reset_rate_limiter.is_rate_limited(
        rate_key,
        config.RATE_LIMIT_RESET_MAX_ATTEMPTS,
        config.RATE_LIMIT_RESET_WINDOW_SECONDS,
    )
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset requests. Please wait {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    password_reset_rate_limiter.record_attempt(rate_key)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({"email": email_clean})
    if doc:
        raw_token, token_hash, expires_at = generate_reset_token()
        await collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "password_reset_token_hash": token_hash,
                    "password_reset_expires_at": expires_at,
                    "password_reset_used": False,
                }
            },
        )
        logger.info(f"[AUTH] Password reset token for {email_clean}: {raw_token}")

    # Constant message prevents email enumeration
    return MessageResponse(
        status="success",
        message="If an account with that email exists, password reset instructions have been sent.",
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
    description="Reset password using a valid, unexpired reset token. Revokes previous active sessions.",
)
async def reset_password(payload: ResetPasswordRequest):
    validate_password_complexity(payload.new_password)

    token_hash = hash_token(payload.token.strip())

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({
        "password_reset_token_hash": token_hash,
        "password_reset_used": False,
    })

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used password reset token.",
        )

    expires_at = doc.get("password_reset_expires_at")
    if not expires_at or expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new reset link.",
        )

    # Hash new password and record password change timestamp (invalidates active JWTs)
    new_hash = hash_password(payload.new_password)
    now = datetime.now(timezone.utc)

    await collection.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "password_hash": new_hash,
                "password_changed_at": now,
                "password_reset_used": True,
            },
            "$unset": {
                "password_reset_token_hash": "",
                "password_reset_expires_at": "",
            },
        },
    )

    return MessageResponse(
        status="success",
        message="Password has been reset successfully. Please log in with your new password.",
    )


@router.get(
    "/me",
    response_model=StudentResponse,
    summary="Get authenticated student profile",
    description="Retrieve the currently authenticated student profile using Bearer token.",
)
async def get_me(current_student: dict = Depends(get_current_student)):
    return _student_to_response(current_student)


@router.get(
    "/current",
    response_model=StudentResponse,
    summary="Get current student profile",
    description="Refactored endpoint: requires valid Bearer authentication (replaces insecure DB scan).",
)
async def get_current_student_endpoint(current_student: dict = Depends(get_current_student)):
    return _student_to_response(current_student)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Get a student's profile",
    description="Requires authentication. Returns full profile for owner, or sanitized view for others.",
)
async def get_student(
    student_id: str,
    current_student: dict = Depends(get_current_student),
):
    target_id = _object_id_or_404(student_id)
    is_owner = str(current_student["_id"]) == str(target_id)

    if is_owner:
        return _student_to_response(current_student)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]
    doc = await collection.find_one({"_id": target_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Redact sensitive information when viewing another user's profile
    return _student_to_response(doc, public_view=True)


@router.put(
    "/{student_id}/profile",
    response_model=StudentResponse,
    summary="Update a student's profile",
    description="Requires authentication and ownership verification (prevents BOLA/IDOR).",
)
async def update_student_profile(
    student_id: str,
    payload: StudentProfileUpdate,
    current_student: dict = Depends(get_current_student),
):
    require_student_ownership(student_id, current_student)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    update_data = {
        "skills": payload.skills,
        "preferred_domain": payload.preferred_domain,
        "preferred_location": payload.preferred_location,
        "university": payload.university,
        "field_of_study": payload.field_of_study,
        "domain_interests": payload.domain_interests,
    }
    if payload.name is not None:
        update_data["name"] = payload.name
    if payload.first_name is not None:
        update_data["first_name"] = payload.first_name
    if payload.last_name is not None:
        update_data["last_name"] = payload.last_name

    result = await collection.find_one_and_update(
        {"_id": _object_id_or_404(student_id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    return _student_to_response(result)


@router.post(
    "/{student_id}/recompute",
    summary="Recompute recommendations for a student",
    description="Requires authentication and ownership verification.",
)
async def recompute_recommendations(
    student_id: str,
    current_student: dict = Depends(get_current_student),
):
    require_student_ownership(student_id, current_student)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]
    listings_coll = db[config.LISTINGS_COLLECTION]

    doc = await collection.find_one({"_id": _object_id_or_404(student_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    student_skills = set(s.strip().lower() for s in doc.get("skills", []) if s)

    matched_items = []
    near_miss_items = []
    total_evaluated = 0

    async for listing in listings_coll.find({"skills.0": {"$exists": True}}):
        total_evaluated += 1
        req_skills = listing.get("skills", [])
        if not req_skills:
            continue

        matched = [s for s in req_skills if s.lower() in student_skills]
        missing = [s for s in req_skills if s.lower() not in student_skills]
        score = round((len(matched) / len(req_skills)) * 100)

        item = {
            "id": str(listing["_id"]),
            "title": listing.get("title", "Opportunity"),
            "company": listing.get("company") or (listing.get("source", "").capitalize()),
            "source": listing.get("source", "scraper"),
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": missing,
        }

        if score >= 70:
            matched_items.append(item)
        elif score >= 40:
            near_miss_items.append(item)

    matched_items.sort(key=lambda x: x["match_score"], reverse=True)
    near_miss_items.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "status": "success",
        "message": f"Successfully recomputed recommendations across {total_evaluated} listings",
        "student_id": student_id,
        "student_name": doc.get("name"),
        "timestamp": datetime.utcnow().isoformat(),
        "stats": {
            "total_evaluated": total_evaluated,
            "matched_count": len(matched_items),
            "near_miss_count": len(near_miss_items),
        },
        "top_matches": matched_items[:5],
        "top_near_misses": near_miss_items[:5],
    }


@router.put(
    "/{student_id}/skills",
    response_model=StudentResponse,
    summary="Update a student's skill list",
    description="Requires authentication and ownership verification.",
)
async def update_student_skills(
    student_id: str,
    payload: StudentSkillsUpdate,
    current_student: dict = Depends(get_current_student),
):
    require_student_ownership(student_id, current_student)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    result = await collection.find_one_and_update(
        {"_id": _object_id_or_404(student_id)},
        {"$set": {"skills": payload.skills}},
        return_document=ReturnDocument.AFTER,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    return _student_to_response(result)


@router.put(
    "/{student_id}/preferences",
    response_model=StudentResponse,
    summary="Update a student's preferred domain/location",
    description="Requires authentication and ownership verification.",
)
async def update_student_preferences(
    student_id: str,
    payload: StudentPreferencesUpdate,
    current_student: dict = Depends(get_current_student),
):
    require_student_ownership(student_id, current_student)

    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    result = await collection.find_one_and_update(
        {"_id": _object_id_or_404(student_id)},
        {"$set": {
            "preferred_domain": payload.preferred_domain,
            "preferred_location": payload.preferred_location,
        }},
        return_document=ReturnDocument.AFTER,
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    return _student_to_response(result)