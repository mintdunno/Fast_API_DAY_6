from pydantic import BaseModel


class ExternalPost(BaseModel):
    userId: int
    id: int
    title: str
    body: str
