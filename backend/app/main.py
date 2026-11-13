import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("SURAJSONG_DB_PATH", str(APP_DIR / "surajsong.db")))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
ACESTEP_WORKER_URL = os.getenv("ACESTEP_WORKER_URL", "").rstrip("/")

app = FastAPI(
    title="SurajSong API",
    version="0.2.0",
    description="Free-first backend for original Bengali and Hindi AI music projects.",
)


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                language TEXT NOT NULL,
                lyrics TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL DEFAULT 4
            )
        """)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(songs)")}
        if "duration_minutes" not in columns:
            connection.execute("ALTER TABLE songs ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 4")


init_db()


class SongRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    language: Literal["bn", "hi"] = "bn"
    duration_minutes: int = Field(default=4, ge=3, le=5)


class MusicRequest(BaseModel):
    style_prompt: str = Field(default="Original melodic song, expressive vocals, polished studio arrangement", max_length=1000)
    seed: int | None = None


async def generate_lyrics(topic: str, language: str, duration: int) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Lyrics AI is not configured. Add GEMINI_API_KEY to the backend environment; never put it in the Android app.",
        )

    language_name = "Bengali" if language == "bn" else "Hindi"
    prompt = f"""
Write complete, original {language_name} song lyrics for a {duration}-minute song.
Topic: {topic}
Requirements:
- Use natural, singable language and clear emotional storytelling.
- Structure with [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Verse 2], [Bridge], [Final Chorus], [Outro].
- Make the chorus memorable and repeat it where appropriate.
- Do not imitate or mention any existing artist, song, or copyrighted lyrics.
- Output only the lyrics, in {language_name}.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                url,
                headers={"x-goog-api-key": GEMINI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.85, "maxOutputTokens": 4096},
                },
            )
        response.raise_for_status()
        payload = response.json()
        return payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    except httpx.HTTPStatusError as error:
        # Do not echo upstream bodies: provider responses can contain sensitive request details.
        raise HTTPException(
            status_code=502,
            detail=f"Lyrics provider returned HTTP {error.response.status_code}. Check the Gemini API key, model access, and quota in the backend environment.",
        ) from error
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as error:
        # Keep diagnostics useful without returning request headers or credentials to the Android client.
        safe_message = "Invalid Gemini API configuration or network response."
        raise HTTPException(status_code=502, detail=f"Lyrics generation failed: {safe_message}") from error


@app.get("/health")
def health():
    return {"status": "ok", "service": "surajsong-api", "version": "0.2.0"}


@app.get("/api/v1/config")
def public_config():
    return {
        "languages": ["bn", "hi"],
        "target_song_duration_minutes": {"min": 3, "max": 5},
        "genre_selection": "automatic",
        "singer_selection": "automatic",
        "providers": {
            "lyrics": {"name": "Gemini API", "configured": bool(GEMINI_API_KEY), "model": GEMINI_MODEL},
            "music": {"name": "ACE-Step self-hosted worker", "configured": bool(ACESTEP_WORKER_URL), "license": "Apache-2.0 project; verify each model checkpoint license"},
            "video": {"name": "FFmpeg", "configured": True},
            "images": {"name": "ComfyUI self-hosted worker", "configured": False},
            "youtube": {"name": "YouTube Data API v3", "configured": False},
        },
        "free_tier_note": "Free API quotas are limited and may change. Music/image generation needs self-hosted GPU hardware or a separately available free GPU runtime.",
    }


@app.post("/api/v1/songs")
async def create_song(request: SongRequest):
    lyrics = await generate_lyrics(request.topic, request.language, request.duration_minutes)
    song_id = str(uuid.uuid4())
    status = "lyrics_ready_waiting_for_music_worker"
    created_at = datetime.now(timezone.utc).isoformat()
    with db() as connection:
        connection.execute(
            "INSERT INTO songs (id, topic, language, lyrics, status, created_at, duration_minutes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (song_id, request.topic, request.language, lyrics, status, created_at, request.duration_minutes),
        )
    return {
        "id": song_id,
        "topic": request.topic,
        "language": request.language,
        "duration_minutes": request.duration_minutes,
        "lyrics": lyrics,
        "status": status,
        "music_worker_configured": bool(ACESTEP_WORKER_URL),
        "created_at": created_at,
    }


@app.get("/api/v1/songs/{song_id}")
def get_song(song_id: str):
    with db() as connection:
        row = connection.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Song project not found")
    return dict(row)


@app.post("/api/v1/songs/{song_id}/generate-music")
async def generate_music(song_id: str, request: MusicRequest):
    if not ACESTEP_WORKER_URL:
        raise HTTPException(
            status_code=503,
            detail="Music worker is not configured. Deploy the ACE-Step worker on a GPU host and set ACESTEP_WORKER_URL.",
        )
    with db() as connection:
        row = connection.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Song project not found")

    try:
        async with httpx.AsyncClient(timeout=900) as client:
            response = await client.post(
                f"{ACESTEP_WORKER_URL}/generate",
                json={
                    "project_id": song_id,
                    "lyrics": row["lyrics"],
                    "language": row["language"],
                    "duration_minutes": row["duration_minutes"],
                    "style_prompt": request.style_prompt,
                    "seed": request.seed,
                },
            )
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"ACE-Step worker request failed: {error}") from error

    status = "music_generation_submitted"
    with db() as connection:
        connection.execute("UPDATE songs SET status = ? WHERE id = ?", (status, song_id))
    return {"id": song_id, "status": status, "worker_result": result}
