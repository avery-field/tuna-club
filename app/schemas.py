from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    is_artist: bool = False

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    is_artist: bool
    created_at: datetime
    class Config:
        orm_mode = True

class SnippetOut(BaseModel):
    id: int
    artist_id: int
    title: str
    genre: Optional[str] = None
    spotify_url: Optional[str] = None
    audio_url: str
    created_at: datetime
    class Config:
        orm_mode = True

class InteractionCreate(BaseModel):
    user_id: int
    snippet_id: int
    action: str
