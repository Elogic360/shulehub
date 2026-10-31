from pydantic import BaseModel, Field


class UssdCallbackRequest(BaseModel):
    sessionId: str
    serviceCode: str
    phoneNumber: str
    text: str = ""
