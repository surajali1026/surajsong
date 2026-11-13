# SurajSong — AI Bengali & Hindi Music Studio

Android-first studio for creating original Bengali/Hindi songs and music videos.

## Product workflow
1. Enter a topic and choose Bengali or Hindi.
2. Generate structured, original lyrics.
3. Generate a 3–5 minute song with an AI singer and arrangement.
4. Create song-matched images and a thumbnail.
5. Render an MP4 with FFmpeg.
6. Optionally upload or schedule it to the user's YouTube channel after OAuth consent.

## Free-first, best-quality architecture

| Stage | Selected technology | Cost approach |
|---|---|---|
| Lyrics | Gemini Developer API (model configurable) | Start on eligible free tier; quotas and terms may change |
| Music + vocals | ACE-Step self-hosted worker | Open-source project; needs GPU compute and checkpoint-license review |
| Images | ComfyUI + separately licensed checkpoint | Self-host to avoid per-image API fees |
| MP4 | FFmpeg | Open-source processing on worker |
| YouTube | YouTube Data API v3 + OAuth | API quota based; user's explicit authorization |

**Important:** "Free" means no paid per-call API plan is required for the self-hosted models; it does not mean unlimited free GPU hosting. A suitable GPU, storage, electricity and deployment may still cost money. ACE-Step's own project notes that less-common languages can underperform; Bengali/Hindi vocal quality must be tested with sample songs before promising studio-grade results. Check the exact model checkpoint's license before commercial publishing.

## Current implementation
- Native Android app connects to a configurable HTTPS backend URL.
- Android app can submit a Bengali/Hindi topic and display generated lyrics.
- FastAPI backend exposes health/config, lyrics/song creation, project retrieval and ACE-Step worker handoff endpoints.
- Gemini API key is read only from backend environment variables; never store provider secrets in the APK.
- SQLite project storage is currently for development. Production needs persistent storage or PostgreSQL, authentication and a job queue.
- Music generation, ComfyUI image generation, MP4 rendering and YouTube OAuth/upload are planned integration steps, not yet fully wired end-to-end.

## Backend setup
See [backend/README.md](backend/README.md) and [backend/.env.example](backend/.env.example).

## Android build
GitHub Actions builds a debug APK. Open the latest successful run and download the `surajsong-debug-apk` artifact.

## Repository layout
- `android/`: Kotlin + Jetpack Compose app
- `backend/`: FastAPI API and provider adapters
- `.github/workflows/`: Android CI
