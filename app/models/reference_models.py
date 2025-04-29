from pydantic import BaseModel
from typing import List, Optional

class SurfManeuver(BaseModel):
    name: str
    level: str
    description: str
    key_mechanics: List[str]
    ideal_moment_keywords: List[str]
    reference_clip: Optional[str] = None
    frames: List[str]


class SurfTechnique(BaseModel):
    name: str
    level: str
    description: str
    key_focus: List[str]
    common_errors: List[str]

