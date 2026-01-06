from typing import List, Optional
from pydantic import BaseModel

class Question(BaseModel):
    id: int
    type: str  # "choice" | "fill" | "short"
    stem: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
