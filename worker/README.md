# ACE-Step GPU worker deployment

SurajSong's Render service is the lightweight API/backend. **Do not deploy the GPU model on Render's free web service.** Deploy ACE-Step on a GPU host that supports CUDA and expose its REST API privately or over HTTPS.

## Why this avoids the Hugging Face Space error

The app's music request uses ACE-Step's native `POST /release_task` endpoint with `thinking=false`, `use_format=false`, and explicit song metadata. ACE-Step documents that `thinking=false` skips the optional 5Hz LM code-generation path. This means the 5Hz LM does not need to initialize for this request. The main DiT music model still has to load on a compatible GPU.

## GPU worker setup

Use a GPU machine with Python 3.11 or 3.12, CUDA-compatible PyTorch, and enough VRAM. ACE-Step's install guide lists 4 GB VRAM as the minimum for DiT-only mode; 8 GB or more is a more practical starting point for longer songs and memory headroom. Actual speed depends on GPU, model, and host.

On the GPU host:

```bash
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5
```

Configure the service environment (use a strong, unique API key and store it only in the host's secret manager):

```bash
export ACESTEP_API_HOST=0.0.0.0
export ACESTEP_API_PORT=8001
export ACESTEP_API_KEY='GENERATE_A_LONG_RANDOM_SECRET'
export ACESTEP_CONFIG_PATH=acestep-v15-turbo
export ACESTEP_INIT_LLM=false
export ACESTEP_USE_FLASH_ATTENTION=true
```

Install and launch the official REST API:

```bash
uv sync
uv run acestep-api
```

The official API listens on port 8001 by default. Confirm `GET /health` returns a healthy response and `GET /v1/models` lists the loaded DiT model. Do not expose port 8001 without API-key authentication and HTTPS.

## Connect Render to the worker

In the Render dashboard, open the `surajsong-api` service → Environment and set:

- `ACESTEP_WORKER_URL`: the GPU worker's HTTPS REST API base URL (not a Gradio Space URL; no trailing slash required).
- `ACESTEP_API_KEY`: exactly the same secret configured as `ACESTEP_API_KEY` on the GPU host.

Redeploy the Render backend after saving. Keep both secrets private. Never put either value in Android, GitHub commits, screenshots, or public logs.

## Test the worker before connecting the app

```bash
curl -H "Authorization: Bearer $ACESTEP_API_KEY" "$ACESTEP_WORKER_URL/health"
```

Then test a short 30-second DiT-only task before trying the app's full 3–5 minute songs:

```bash
curl -X POST "$ACESTEP_WORKER_URL/release_task" \
  -H "Authorization: Bearer $ACESTEP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"soft Bengali acoustic pop, gentle guitar and strings","lyrics":"[Verse 1]\nA short test lyric","thinking":false,"use_format":false,"use_cot_caption":false,"use_cot_language":false,"vocal_language":"bn","audio_format":"mp3","audio_duration":30,"bpm":96,"key_scale":"C Major","time_signature":"4","inference_steps":8,"batch_size":1}'
```

The response should contain `data.task_id`. Poll `POST /query_result` with that task ID until the task succeeds, then retrieve the MP3 from the returned `/v1/audio?path=...` URL. These are the official ACE-Step API endpoints.

## Cost and safety

- No GPU instance is started by this repository. Choose a free/owned GPU first if available.
- If the provider requires payment, check the hourly rate, storage charges, idle shutdown, and estimated runtime before starting it. Do not enable paid compute without the account owner's approval.
- A free Hugging Face Space or free notebook is not a guaranteed always-on private production worker. Treat it as a manual test only.
- Bengali/Hindi singing quality and exact 3–5 minute duration must be validated with test jobs before public use.
- The current backend uses SQLite; production needs persistent storage and authentication before serving multiple users.
