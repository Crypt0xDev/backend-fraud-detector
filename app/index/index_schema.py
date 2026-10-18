from pydantic import BaseModel


class IndexOut(BaseModel):
    name: str
    version: str
    docs: str
    health: str
