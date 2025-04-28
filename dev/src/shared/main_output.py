from pydantic import BaseModel, Field


class ErrorOutput(BaseModel):
    message: str = Field(description="The output that is given to the user")


class SuccessOutput(BaseModel):
    message: str = Field(
        description="The reply that is send to the user, with included citations"
    )
