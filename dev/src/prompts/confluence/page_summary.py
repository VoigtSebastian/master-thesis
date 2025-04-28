from typing import Optional
from pydantic import BaseModel, Field


class PageSummary(BaseModel):
    summary: Optional[str] = Field(
        description="An optional very concise summary of a Confluence page"
    )
