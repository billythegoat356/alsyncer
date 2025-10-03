from pydantic import BaseModel





class CharAlignment(BaseModel):
    character: str
    duration: int | float # ms

Alignment = list[CharAlignment]