from typing import (
    List,
    Literal,
)
from pydantic import BaseModel, field_validator

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class Conversation(BaseModel):
    conversation: List[Message]

    @field_validator("conversation")
    def conversation_format_validator(cls, conv: List[Message]):
        # Validate last message is a user message
        if conv[-1].role != "user": 
            raise ValueError("The last message must be a user message")
        
        # Validate messages alternate between user and ai
        if conv[0].role == "system":
            for i, message in enumerate(conv[1:], start=1):
                if (i%2 == 1 and message.role == "user"):
                    continue
                elif (i%2 == 0 and message.role == "assistant"):
                    continue
                else:
                    raise KeyError("Messages must alternate between assistant and user")
        if conv[0].role == "user":
            for i, message in enumerate(conv[1:], start=1):
                if (i%2 == 0 and message.role == "user"):
                    continue
                elif (i%2 == 1 and message.role == "assistant"):
                    continue
                else:
                    raise KeyError("Messages must alternate between assistant and user")
        
        return conv