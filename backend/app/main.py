from fastapi import FastAPI

app = FastAPI(
    title="SurajSong API",
    version="0.1.0",
    description="Backend API for the SurajSong Android AI Music Studio.",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "surajsong-api",
        "generation": "not_configured",
    }


@app.get("/api/v1/config")
def public_config():
    return {
        "languages": ["bn", "hi"],
        "target_song_duration_minutes": {"min": 3, "max": 5},
        "genre_selection": "automatic",
        "singer_selection": "automatic",
        "features": {
            "lyrics": "planned",
            "music": "planned",
            "vocals": "planned",
            "images": "planned",
            "video": "planned",
            "youtube_upload": "planned",
        },
    }
