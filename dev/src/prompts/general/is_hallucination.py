from pydantic import BaseModel, Field


class Hallucination(BaseModel):
    observations: str = Field(
        description="Very concise observation of the input and what it means for your final decision - maximum 50 words"
    )
    hallucination: bool = Field(description="true if the claim does not hold")
