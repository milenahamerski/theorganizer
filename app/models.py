from pydantic import BaseModel
from typing import Optional

class Book(BaseModel):
    id: Optional[int] = None
    title: str
    author: str
    year: Optional[int] = None
    image_url: Optional[str] = None
