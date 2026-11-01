# pydantic
from pydantic import BaseModel

class BaseSchema(BaseModel):
    """Base de los esquemas de entrada: quita espacios y rechaza campos desconocidos"""

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
    }
