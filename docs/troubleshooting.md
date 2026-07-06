# Troubleshooting

## Backend

### `ModuleNotFoundError: No module named 'app'`
Run uvicorn from the `backend/` directory and ensure the working
directory contains the `app/` package.

### `pydantic_settings.errors.SettingsError`
The `.env` file contains an invalid value. Re-generate from
`.env.example` and adjust only the values you need.

### Ollama timeouts
Increase `LLM_TIMEOUT_SEC` in `.env` or pull a smaller model:
`ollama pull gemma2:2b`.

## Frontend

### `Failed to fetch` on every request
The frontend cannot reach the API. Check `NEXT_PUBLIC_API_URL` and
verify CORS in the backend allows the frontend origin.

### Tailwind classes not applied
Restart the dev server. Tailwind only scans files that exist when it
starts.

## Docker

### `Bind for 0.0.0.0:8000 failed: port already in use`
Stop the process listening on port 8000 or change `APP_PORT`.

### ChromaDB errors
Delete the `chroma_data` volume and restart:
`docker compose down -v && docker compose up --build`.
