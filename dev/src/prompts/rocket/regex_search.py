from pydantic import BaseModel, Field


class RegexSearch(BaseModel):
    observations: str = Field(
        description="Very concise observation of the input and what it means for your final decision - maximum 50 words"
    )
    keywords: list[str] = Field(description="The keywords you want to search for")
