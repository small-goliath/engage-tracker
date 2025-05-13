from pydantic.main import BaseModel

class InstagramLogin(BaseModel):
    verification_code: str

class LimitByWeeks(BaseModel):
    limit: str