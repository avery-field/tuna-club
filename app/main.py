import os
import shutil
from uuid import uuid4
from typing import List

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas
from .database import engine, Base, get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Snippet Discovery MVP")

# static serving for uploaded audio
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# allow CORS during development (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create DB tables (simple approach for MVP)
Base.metadata.create_all(bind=engine)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

@app.post("/users/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # naive uniqueness checks
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
        is_artist=user.is_artist,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # simple MVP response (replace with JWT later)
    return {"user_id": user.id, "username": user.username}

@app.post("/snippets/", response_model=schemas.SnippetOut)
def upload_snippet(
    artist_id: int = Form(...),
    title: str = Form(...),
    genre: str = Form(None),
    spotify_url: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    artist = db.query(models.User).filter(models.User.id == artist_id, models.User.is_artist == True).first()
    if not artist:
        raise HTTPException(status_code=400, detail="Artist not found or not an artist")

    # save file locally (for MVP)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_snippet = models.Snippet(
        artist_id=artist_id,
        title=title,
        genre=genre,
        spotify_url=spotify_url,
        audio_path=file_path,
    )
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)

    audio_url = f"/uploads/{filename}"
    return schemas.SnippetOut(
        id=db_snippet.id,
        artist_id=db_snippet.artist_id,
        title=db_snippet.title,
        genre=db_snippet.genre,
        spotify_url=db_snippet.spotify_url,
        audio_url=audio_url,
        created_at=db_snippet.created_at,
    )

@app.get("/feed/", response_model=List[schemas.SnippetOut])
def get_feed(limit: int = 20, db: Session = Depends(get_db)):
    snippets = db.query(models.Snippet).order_by(models.Snippet.created_at.desc()).limit(limit).all()
    results = []
    for s in snippets:
        filename = os.path.basename(s.audio_path)
        audio_url = f"/uploads/{filename}"
        results.append(
            schemas.SnippetOut(
                id=s.id,
                artist_id=s.artist_id,
                title=s.title,
                genre=s.genre,
                spotify_url=s.spotify_url,
                audio_url=audio_url,
                created_at=s.created_at,
            )
        )
    return results

@app.post("/interactions/")
def create_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == interaction.user_id).first()
    snippet = db.query(models.Snippet).filter(models.Snippet.id == interaction.snippet_id).first()
    if not user or not snippet:
        raise HTTPException(status_code=404, detail="User or snippet not found")
    db_i = models.Interaction(user_id=interaction.user_id, snippet_id=interaction.snippet_id, action=interaction.action)
    db.add(db_i)
    db.commit()
    db.refresh(db_i)
    return {"status": "ok", "id": db_i.id}
