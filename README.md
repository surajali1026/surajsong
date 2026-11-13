# SurajSong — AI Bengali Music Studio

An Android-first AI music and music-video creation studio.

## Product goals
- Generate original Bengali and Hindi lyrics from a topic.
- Automatically select a suitable genre, mood, tempo and AI singer.
- Generate a complete 3–5 minute song and export MP3.
- Analyze the song and create matching AI images plus one thumbnail.
- Render an MP4 music video with transitions and audio synchronization.
- Connect the user's YouTube channel and upload or schedule videos after explicit authorization.

## Important implementation principles
- Android is the primary user interface. Users should be able to manage the complete workflow from the Android app.
- Heavy generative models may need a separate worker/server or a supported hosted inference provider; do not assume a phone can run every model.
- Prefer open-source models and free tiers, but clearly show limits, queue status and any possible costs. Never silently use paid APIs.
- Keep provider integrations behind interfaces so models can be changed without rewriting the app.
- Keep API keys and YouTube OAuth secrets out of the APK.
- Only generate or upload audio the user owns or is authorized to use. Use original lyrics, music and properly licensed assets.

## Initial development milestone
Build the native Android shell, topic/language input, project list, backend connection interface and CI build. AI generation providers will be integrated in later milestones after their licensing, hardware and free-tier constraints are verified.

## Repository layout
- `android/`: Kotlin + Jetpack Compose application
- `backend/`: FastAPI service scaffold and future generation jobs
- `.github/workflows/`: Android CI

## Build
The GitHub Actions workflow builds the Android debug APK using Gradle 8.9 and JDK 17.

## Planned phases
1. Android app foundation and CI.
2. Lyrics generation (Bengali/Hindi).
3. Music + singing model adapter and MP3 export.
4. Song analysis, AI images and thumbnail.
5. FFmpeg-based MP4 rendering.
6. YouTube OAuth, upload and scheduling.
