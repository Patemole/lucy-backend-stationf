from pydantic import BaseModel

class StudentProfile(BaseModel):
    academic_advisor: str
    faculty: str
    major: list[str]
    minor: list[str]
    name: str
    university: str
    year: str