from pydantic import BaseModel
from typing import Optional


class InputQuery(BaseModel):
    # course_name: str # TO BE DEPRECATED
    course_id: str
    chat_id: str
    username: str
    message: str
    university: str
    student_profile: str
    faculty: list[str]
    major: Optional[list[str]]
    minor: Optional[list[str]]
    year: str


class InputQueryAI(BaseModel):
    chatSessionId: str
    courseId: str
    username: str
    message: str
    type: str
    uid: str
    input_message: str
    university: str
        