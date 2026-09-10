from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from api.auth import hash_password, verify_password
from api.config import config
from api.database import get_database
from api.models import (
    StudentLogin,
    StudentPreferencesUpdate,
    StudentProfileUpdate,
    StudentRegister,
    StudentResponse,
    StudentSkillsUpdate,
)

router = APIRouter(prefix="/students", tags=["Students"])


def _student_to_response(doc: dict) -> StudentResponse:
    """Map a MongoDB student document to the public-facing response model.
    Deliberately excludes password_hash - that field never leaves this file."""
    first_name = doc.get("first_name")
    last_name = doc.get("last_name")
    if not first_name and doc.get("name"):
        parts = doc["name"].strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    return StudentResponse(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        first_name=first_name,
        last_name=last_name,
        email=doc.get("email", ""),
        skills=doc.get("skills", []),
        preferred_domain=doc.get("preferred_domain"),
        preferred_location=doc.get("preferred_location"),
        university=doc.get("university"),
        field_of_study=doc.get("field_of_study"),
        domain_interests=doc.get("domain_interests", []),
        created_at=doc.get("created_at"),
    )


def _object_id_or_404(student_id: str) -> ObjectId:
    try:
        return ObjectId(student_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid student ID format")


@router.post(
    "/register",
    response_model=StudentResponse,
    status_code=201,
    summary="Register a new student",
    description="Create a new student account with an optional starting skill list.",
)
async def register_student(payload: StudentRegister):
    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    existing = await collection.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    first_name = payload.first_name
    last_name = payload.last_name
    if not first_name and payload.name:
        parts = payload.name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    student_doc = {
        "name": payload.name,
        "first_name": first_name,
        "last_name": last_name,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
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
        # Belt-and-suspenders: the find_one check above handles the
        # common case, this catches a race if two requests land at once
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    student_doc["_id"] = result.inserted_id
    return _student_to_response(student_doc)


@router.post(
    "/login",
    response_model=StudentResponse,
    summary="Log in a student",
    description="Verify email/password and return the student's profile.",
)
async def login_student(payload: StudentLogin):
    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({"email": payload.email.lower()})
    if not doc or not verify_password(payload.password, doc["password_hash"]):
        # Same error for "no such email" and "wrong password" on purpose -
        # confirming which one it was would leak whether an email is registered
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return _student_to_response(doc)


@router.get(
    "/current",
    response_model=StudentResponse,
    summary="Get current or default student profile",
    description="Retrieve the active student profile from the database.",
)
async def get_current_student():
    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]
    doc = await collection.find_one(sort=[("_id", -1)])
    if not doc:
        raise HTTPException(status_code=404, detail="No registered student found")
    return _student_to_response(doc)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Get a student's profile",
)
async def get_student(student_id: str):
    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    doc = await collection.find_one({"_id": _object_id_or_404(student_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")

    return _student_to_response(doc)


@router.put(
    "/{student_id}/profile",
    response_model=StudentResponse,
    summary="Update a student's profile",
    description="Update a student's full profile including skills, preferred domain, location, university, and domains.",
)
async def update_student_profile(student_id: str, payload: StudentProfileUpdate):
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
        raise HTTPException(status_code=404, detail="Student not found")

    return _student_to_response(result)


@router.post(
    "/{student_id}/recompute",
    summary="Recompute recommendations for a student",
    description="Trigger a fresh pass of the recommendation engine with updated profile skills and interests.",
)
async def recompute_recommendations(student_id: str):
    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]
    listings_coll = db[config.LISTINGS_COLLECTION]

    doc = await collection.find_one({"_id": _object_id_or_404(student_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")

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
    description=(
        "Replace a student's full skill list. This is what keeps a "
        "student's profile in sync with what they select in the "
        "dashboard, and is what the recommendation engine will read "
        "from to compute matches."
    ),
)
async def update_student_skills(student_id: str, payload: StudentSkillsUpdate):
    db = get_database()
    collection = db[config.STUDENTS_COLLECTION]

    result = await collection.find_one_and_update(
        {"_id": _object_id_or_404(student_id)},
        {"$set": {"skills": payload.skills}},
        return_document=ReturnDocument.AFTER,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Student not found")

    return _student_to_response(result)


@router.put(
    "/{student_id}/preferences",
    response_model=StudentResponse,
    summary="Update a student's preferred domain/location",
    description="Set or change preferred_domain and preferred_location after registration.",
)
async def update_student_preferences(student_id: str, payload: StudentPreferencesUpdate):
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
        raise HTTPException(status_code=404, detail="Student not found")

    return _student_to_response(result)