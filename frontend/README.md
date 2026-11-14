# VERRIER-X frontend

Next.js page with the search form and the blink viewer.

Start the backend first (from `backend/`): `uv run uvicorn app.main:app --port 8000`

Then, from this folder: `npm install` and `npm run dev`, and open http://localhost:3000.

The backend address is set with `NEXT_PUBLIC_API_URL` (see `.env.example`). It defaults to `http://localhost:8000`.

A position can be opened straight from a link: `/?ra=269.4486&dec=4.7685&fov=10&band=2`.
