# Nokshi Threads Ltd. — Crisis to Compliance

Competition gateway for The Jurists. It presents the Nokshi Threads business crisis, the five Bangladesh business Acts and a concept video.

## Stack

- Next.js App Router and React with TypeScript in `app/`.
- FastAPI application in `backend/main.py`. It retrieves passages from local DOCX knowledge files and sends the question, recent conversation, and retrieved passages to Groq using `openai/gpt-oss-120b`.
- Statutory knowledge, scenario facts, and chatbot source documents in `knowledge/`.
- Static media in `public/assets/`.

The `/api/*` Next rewrite proxies requests to FastAPI. By default the web app runs on port 3000 and the API on port 4001.

## Run locally

Requires Node.js 20.9 or newer and Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the environment in PowerShell on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Then install dependencies and start the app:

```bash
npm install
python -m pip install -r requirements.txt
npm run dev
```

Copy `.env.example` to `.env`, then set `GROQ_APIKEY` to your private key and keep `.env` local. You can also adjust the ports there. FastAPI loads this file at startup. Run `npm run dev` to start both the web app and API. For production, build with `npm run build`, then run `npm start`. Set `API_BACKEND_URL` if the API is hosted at a separate address.

The key is read only by FastAPI; never place it in frontend code, commit it, or share it. The DOCX files are read and indexed locally at API startup; the complete documents are not uploaded. Only up to four retrieved passages and the recent conversation are sent to Groq with each question. The chatbot displays only the generated answer, not source lists or model metadata.

The API provides `GET /api/health` and `POST /api/chat`. Chat requests accept a message up to 1,500 characters and up to six prior user/assistant messages. Run `npm test` for the API and document-retrieval tests. This is educational legal information, not legal advice.

## Legal knowledge

The JSON files in `knowledge/laws/` contain short paraphrases, not full statutes. Sources link to the official Bangladesh Laws database. The scenario file records project facts and missing documents. Verify current official texts and actual case documents before making legal conclusions; this is an educational competition project, not legal advice.
