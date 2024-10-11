from pydantic import BaseModel
from typing import Optional


class StudentProfile(BaseModel):
    academic_advisor: Optional[str]
    #schools
    faculty: list[str]
    major: Optional[list[str]]
    minor: Optional[list[str]]
    name: str
    university: str
    year: str
