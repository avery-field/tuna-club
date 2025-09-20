from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_artist = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    snippets = relationship("Snippet", back_populates="artist")
    interactions = relationship("Interaction", back_populates="user")

class Snippet(Base):
    __tablename__ = "snippets"
    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    spotify_url = Column(String, nullable=True)
    audio_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    artist = relationship("User", back_populates="snippets")
    interactions = relationship("Interaction", back_populates="snippet")

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    snippet_id = Column(Integer, ForeignKey("snippets.id", ondelete="CASCADE"))
    action = Column(String, nullable=False)  # 'like', 'skip', 'save'
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    snippet = relationship("Snippet", back_populates="interactions")
