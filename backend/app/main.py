import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("SURAJSONG_DB_PATH", str(APP_DIR / "surajsong.db")))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
# This must be the ACE-Step REST API base URL (normally port 8001), not its Gradio UI URL.
ACESTEP_WORKER_URL = os.getenv("ACESTEP_WORKER_URL", "").rstrip("/")
ACESTEP_API_KEY = os.getenv("ACESTEP_API_KEY", "").strip()

app = FastAPI(
    title="SurajSong API",
    version="0.3.0",
    description="Backend for original Bengali and Hindi AI music projects.",
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
        migrations = {
            "duration_minutes": "ALTER TABLE songs ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 4",
            "music_task_id": "ALTER TABLE songs ADD COLUMN music_task_id TEXT",
            "music_file_path": "ALTER TABLE songs ADD COLUMN music_file_path TEXT",
            "music_error": "ALTER TABLE songs ADD COLUMN music_error TEXT",
        }
        for column, statement in migrations.items():
            if column not in columns:
                connection.execute(statement)


init_db()


class SongRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    language: Literal["bn", "hi"] = "bn"
    duration_minutes: int = Field(default=4, ge=3, le=5)


class MusicRequest(BaseModel):
    style_prompt: str = Field(
        default="Original melodic pop song, expressive lead vocals, warm acoustic guitar, cinematic strings, polished studio arrangement",
        max_length=1000,
    )
    seed: int | None = None


def worker_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if ACESTEP_API_KEY:
        headers["Authorization"] = f"Bearer {ACESTEP_API_KEY}"
    return headers


def worker_data(payload: dict) -> dict:
    if payload.get("code", 200) != 200 or payload.get("error"):
        raise HTTPException(status_code=502, detail="ACE-Step rejected the request. Check worker model initialization and logs.")
    return payload.get("data") or {}


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
        raise HTTPException(
            status_code=502,
            detail=f"Lyrics provider returned HTTP {error.response.status_code}. Check the Gemini API key, model access, and quota in the backend environment.",
        ) from error
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as error:
        raise HTTPException(status_code=502, detail="Lyrics generation failed: invalid provider configuration or network response.") from error


@app.get("/health")
def health():
    return {"status": "ok", "service": "surajsong-api", "version": "0.3.0"}


@app.get("/api/v1/config")
def public_config():
    return {
        "languages": ["bn", "hi"],
        "target_song_duration_minutes": {"min": 3, "max": 5},
        "genre_selection": "automatic",
        "singer_selection": "automatic",
        "providers": {
            "lyrics": {"name": "Gemini API", "configured": bool(GEMINI_API_KEY), "model": GEMINI_MODEL},
            "music": {
                "name": "ACE-Step REST API",
                "configured": bool(ACESTEP_WORKER_URL),
                "api_key_configured": bool(ACESTEP_API_KEY),
                "requires_gpu": True,
                "lm_optional": True,
            },
            "video": {"name": "FFmpeg", "configured": True},
            "images": {"name": "ComfyUI self-hosted worker", "configured": False},
            "youtube": {"name": "YouTube Data API v3", "configured": False},
        },
        "free_tier_note": "ACE-Step needs GPU compute. Generation is submitted without 5Hz LM (thinking=false) so the worker can generate without initializing that optional model.",
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
            detail="ACE-Step GPU worker is not configured yet. Set ACESTEP_WORKER_URL to its REST API URL (port 8001).",
        )
    with db() as connection:
        row = connection.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Song project not found")

    # Explicit metadata plus thinking=false avoids the optional 5Hz LM initialization path.
    # ACE-Step documents that thinking=false uses the DiT text-to-music path without 5Hz LM codes.
    duration_seconds = int(row["duration_minutes"]) * 60
    payload = {
        "prompt": request.style_prompt,
        "lyrics": row["lyrics"],
        "thinking": False,
        "use_format": False,
        "use_cot_caption": False,
        "use_cot_language": False,
        "vocal_language": "Bengali" if row["language"] == "bn" else "Hindi",
        "audio_format": "mp3",
        "audio_duration": duration_seconds,
        "bpm": 96,
        "key_scale": "C Major",
        "time_signature": "4",
        "inference_steps": 8,
        "batch_size": 1,
        "use_random_seed": request.seed is None,
        "seed": request.seed if request.seed is not None else -1,
        "model": "acestep-v15-turbo",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{ACESTEP_WORKER_URL}/release_task",
                headers=worker_headers(),
                json=payload,
            )
        response.raise_for_status()
        result = worker_data(response.json())
        task_id = result.get("task_id")
        if not task_id:
            raise HTTPException(status_code=502, detail="ACE-Step did not return a task_id.")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as error:
        raise HTTPException(status_code=502, detail=f"ACE-Step API returned HTTP {error.response.status_code}. Check the GPU worker.") from error
    except (httpx.HTTPError, ValueError, TypeError) as error:
        raise HTTPException(status_code=502, detail="Could not submit the music job to ACE-Step. Check the worker URL and availability.") from error

    with db() as connection:
        connection.execute(
            "UPDATE songs SET status = ?, music_task_id = ?, music_file_path = NULL, music_error = NULL WHERE id = ?",
            ("music_generation_submitted", task_id, song_id),
        )
    return {"id": song_id, "status": "music_generation_submitted", "task_id": task_id}


@app.get("/api/v1/songs/{song_id}/music-status")
async def music_status(song_id: str):
    with db() as connection:
        row = connection.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Song project not found")
    if not row["music_task_id"]:
        return {"id": song_id, "status": row["status"], "detail": "No music task has been submitted."}
    if not ACESTEP_WORKER_URL:
        raise HTTPException(status_code=503, detail="ACE-Step worker URL is not configured.")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{ACESTEP_WORKER_URL}/query_result",
                headers=worker_headers(),
                json={"task_id_list": [row["music_task_id"]]},
            )
        response.raise_for_status()
        items = worker_data(response.json())
        if not isinstance(items, list) or not items:
            return {"id": song_id, "status": "music_generation_submitted", "task_id": row["music_task_id"]}
        item = items[0]
        state = int(item.get("status", 0))
        if state == 1:
            raw_result = item.get("result") or "[]"
            parsed = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
            file_path = parsed[0].get("file") if parsed else None
            if not file_path:
                raise HTTPException(status_code=502, detail="ACE-Step completed but did not return an audio file.")
            with db() as connection:
                connection.execute(
                    "UPDATE songs SET status = ?, music_file_path = ?, music_error = NULL WHERE id = ?",
                    ("music_ready", file_path, song_id),
                )
            return {"id": song_id, "status": "music_ready", "audio_url": f"/api/v1/songs/{song_id}/audio"}
        if state == 2:
            error_text = str(item.get("error") or "ACE-Step music generation failed.")[:500]
            with db() as connection:
                connection.execute(
                    "UPDATE songs SET status = ?, music_error = ? WHERE id = ?",
                    ("music_failed", error_text, song_id),
                )
            return {"id": song_id, "status": "music_failed", "error": error_text}
        return {"id": song_id, "status": "music_generation_submitted", "task_id": row["music_task_id"]}
    except HTTPException:
        raise
    except httpx.HTTPStatusError as error:
        raise HTTPException(status_code=502, detail=f"ACE-Step status API returned HTTP {error.response.status_code}.") from error
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as error:
        raise HTTPException(status_code=502, detail="Could not read the ACE-Step job status.") from error


@app.get("/api/v1/songs/{song_id}/audio")
async def song_audio(song_id: str):
    with db() as connection:
        row = connection.execute("SELECT music_file_path FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Song project not found")
    if not row["music_file_path"]:
        raise HTTPException(status_code=409, detail="Song audio is not ready yet.")
    if not ACESTEP_WORKER_URL:
        raise HTTPException(status_code=503, detail="ACE-Step worker URL is not configured.")

    audio_url = urljoin(f"{ACESTEP_WORKER_URL}/", row["music_file_path"].lstrip("/"))
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.get(audio_url, headers=worker_headers())
        response.raise_for_status()
        media_type = response.headers.get("content-type", "audio/mpeg")
        return Response(
            content=response.content,
            media_type=media_type,
            headers={"Content-Disposition": f'inline; filename="surajsong-{song_id}.mp3"'},
        )
    except httpx.HTTPStatusError as error:
        raise HTTPException(status_code=502, detail=f"ACE-Step audio endpoint returned HTTP {error.response.status_code}.") from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail="Could not download generated audio from ACE-Step.") from error
