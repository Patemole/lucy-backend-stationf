from typing import Optional, List
from pydantic import BaseModel, validator

class StudentProfile(BaseModel):
    userId: str
    username: str
    name: str
    email: Optional[str] = None
    university: str
    year: str
    academic_advisor: Optional[str] = "Unknown"
    faculty: List[str]
    major: Optional[List[str]] = []
    minor: Optional[List[str]] = []
    studentProfile: Optional[str] = None
    interests: Optional[List[str]] = []
    registered_club_status: Optional[str] = None
    registered_clubs: Optional[str] = None
    profilePicture: Optional[str] = None
    role: Optional[str] = "student"
    createdAt: Optional[str] = "Unknown"
    lastLogin: Optional[str] = "Unknown"

    # 🔥 Nettoyage des listes vides (faculty, major, minor, interests)
    @validator("faculty", "major", "minor", "interests", pre=True, always=True)
    def clean_empty_list(cls, value):
        if isinstance(value, list):
            return [v for v in value if v.strip()]  # Supprime les entrées vides
        return value or []  # Remplace `None` par une liste vide

    # 🔥 Nettoyage du `studentProfile`
    @validator("studentProfile", pre=True, always=True)
    def clean_student_profile(cls, value):
        if value:
            value = value.strip('"')  # Supprime les guillemets inutiles
            value = value.replace("School school", "School")  # Corrige la répétition
        return value


