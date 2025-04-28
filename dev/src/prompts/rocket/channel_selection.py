from pydantic import BaseModel, Field
from typing import Optional


class ChannelSelection(BaseModel):
    extracted_identifiers: Optional[list[str]] = Field(
        description="An optional list of identifiers"
    )
    regular_expression: Optional[str] = Field(
        description="An optional regular expression"
    )
