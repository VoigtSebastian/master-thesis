from pydantic import BaseModel, Field


class Validation(BaseModel):
    observations: str = Field(
        description="Concise observation of the input and what it means for your final decision - maximum 50 words"
    )
    passed: bool = Field(
        description="Final check, set to true if you believe that the input is valid"
    )
