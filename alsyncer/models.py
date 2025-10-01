from pydantic import BaseModel





class CharAlignment(BaseModel):
    character: str
    duration: int # ms

Alignment = list[CharAlignment]