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
| Music + vocals | ACE-Step self-hosted worker | Open-source model; GPU hosting is separate and may cost money |
| Images | ComfyUI + separately licensed checkpoint | Self-host to avoid per-image API fees |
| MP4 | FFmpeg | Open-source processing on worker |
| YouTube | YouTube Data API v3 + OAuth | API quota based; user's explicit authorization |

**Important:** Free software does not mean unlimited free GPU hosting. A suitable GPU, storage, electricity and deployment may still cost money. Bengali/Hindi vocal quality must be tested with sample songs before promising studio-grade results. Check the exact model/checkpoint license before commercial publishing.

## Current implementation
- Native Android app connects to a configurable HTTPS backend URL.
- Android app generates Bengali/Hindi lyrics and can submit a music job.
- FastAPI backend now integrates with ACE-Step's native asynchronous REST API: task submission, status polling and audio proxy.
- The music request disables the optional 5Hz LM path (`thinking=false`) and supplies metadata, so that optional LM does not need to initialize. The main DiT model still requires a compatible GPU.
- Android polls for job completion and exposes a Play generated song action.
- Gemini and ACE-Step API keys stay in backend environment variables; never store provider secrets in the APK.
- GPU worker hosting is not deployed yet; configure it by following [worker/README.md](worker/README.md).

## Backend setup
See [backend/README.md](backend/README.md) and [backend/.env.example](backend/.env.example).

## Android build
GitHub Actions builds a debug APK. Open the latest successful run and download the `surajsong-debug-apk` artifact.

## Repository layout
- `android/`: Kotlin + Jetpack Compose app
- `backend/`: FastAPI API and provider adapters
- `worker/`: ACE-Step GPU worker deployment guide
- `.github/workflows/`: Android CI
