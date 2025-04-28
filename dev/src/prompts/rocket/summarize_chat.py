from pydantic import BaseModel, Field
from typing import Optional


class SummarizeChat(BaseModel):
    summary: Optional[str] = Field(
        description="An optional summary of the chat messages"
    )
