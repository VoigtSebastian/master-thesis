from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Tools(Enum):
    ROCKET_CHAT = "ROCKET"
    CONFLUENCE = "CONFLUENCE"


class ToolChoice(BaseModel):
    observations: str = Field(
        description="Very concise observation of the available information and what it means for your final decision - maximum 100 words"
    )
    tool: set[Tools] = Field(description="A list of tools that should be executed next")
