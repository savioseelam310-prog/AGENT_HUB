# Local Multi-Agent Hub

A local-first AI assistant hub. A Node.js server serves the chat UI and proxies requests to two local Python microservices — an **Email Agent** (Flask) and a **YouTube Trend Agent** (FastAPI) — both powered by a local Ollama model (`qwen3.5:4b`) via `pydantic-ai`.

## 🏗️ Architecture

```
Browser (index.html)
        │
        ▼
Node.js server  ──────►  POST /api/chat  { prompt, mode, model }
        │
        ├── mode: "email"    ──►  Flask service   (email_server.py)      : port 5000
        ├── mode: "youtube"  ──►  FastAPI service  (local_trend_agent.py) : port 5001
        └── mode: "chat"     ──►  Ollama directly, or your own chat route
```

> **Note:** This README assumes the Node.js server exposes a single `/api/chat` endpoint (as called from `index.html`) and forwards the request to the correct Python service based on the `mode` field. Adjust the routing details below to match your actual `server.js`/Express routes if they differ.

## 📦 Tech Stack & Required Libraries

### 🐍 Python Dependencies

```bash
pip install flask pydantic pydantic-ai fastapi uvicorn google-api-python-client python-dotenv
```

* `flask`: Backend framework for the Email Agent service.
* `pydantic` / `pydantic-ai`: Structured output validation and local LLM agent orchestration.
* `fastapi` & `uvicorn`: Backend framework and ASGI server for the YouTube Trend Agent.
* `google-api-python-client`: YouTube Data API v3 client.
* `python-dotenv`: Loads environment variables from a `.env` file.

### ⚛️ Node.js Dependencies

Inside your Node.js project directory:

```bash
npm install express node-fetch cors dotenv
```

* `express`: Serves `index.html` and hosts the `/api/chat` proxy endpoint.
* `node-fetch`: Forwards requests from Node to the Python microservices.
* `cors`: Enables cross-origin requests between frontend and backend during development.
* `dotenv`: Loads Node-side environment variables (service ports/URLs).

### 🌐 Frontend

`index.html` is a single static page (no build step) that uses:
* `marked.js` (via CDN) for rendering Markdown responses.
* Vanilla JS `fetch` to call `/api/chat`.

## 🚀 Getting Started & Installation

### Prerequisites

1. **Node.js & npm** installed.
2. **Python 3.10+** installed.
3. **Ollama** installed locally with the model pulled:

```bash
ollama pull qwen3.5:4b
```

4. A **Google Cloud project** with the YouTube Data API v3 enabled, and an API key for `local_trend_agent.py`.
5. A **Gmail account** with an [App Password](https://support.google.com/accounts/answer/185833) generated for `email_server.py` (do not use your normal Gmail password).

### 🔐 Security setup (do this first)

Both Python files  have secrets key (a Gmail app password and a YouTube API key). Before running or committing this project:


1. Move them into a `.env` file at the project root:

```env
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_new_app_password
YOUTUBE_API_KEY=your_new_youtube_api_key
```

3. Update `email_server.py` and `local_trend_agent.py` to read these via `os.getenv(...)` instead of hardcoded strings.

### 1. Clone the repository

```bash
git clone https://github.com/savioseelam310-prog/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Python services setup

Create and activate a virtual environment:

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

Install dependencies:

```bash
pip install flask pydantic pydantic-ai fastapi uvicorn google-api-python-client python-dotenv
```

Start the **Email Agent** (Flask, port 5000):

```bash
python email_server.py
```

Start the **YouTube Trend Agent** (FastAPI, port 5001), in a separate terminal:

```bash
python local_trend_agent.py
```

### 3. Node.js server setup

In a third terminal, from your Node project directory:

```bash
npm install
node server.js
```

(The Node server serves `index.html` and proxies to the two Python services above — by default this project expects it on `http://localhost:3000`.)

### 4. Open the app

Navigate to:

```
http://localhost:3000
```

Pick a mode from the dropdown (**Standard Chat**, **Email Agent**, **YouTube Agent**) and type an instruction.

## ⚙️ Service Reference

| Service | Port | Framework | Purpose |
|---|---|---|---|
| Node.js server | 3000 | Express (assumed) | Serves UI, routes `/api/chat` to the right backend |
| Email Agent | 5000 | Flask | `POST /api/send-email-agent` — turns a prompt into a structured email and sends it via Gmail SMTP |
| YouTube Trend Agent | 5001 | FastAPI | `POST /api/youtube-agent` — searches trending YouTube videos and can open one in the browser |

## 💻 Usage Modes

* **💬 Standard Chat** — talks directly to the local `qwen3.5:4b` model via Ollama.
* **📧 Email Agent** — describe an email in plain language (e.g. *"email jane@example.com about rescheduling Friday's meeting"*); the agent extracts `to_email`, `subject`, and `body`, then sends it.
* **📺 YouTube Agent** — ask for trending videos on a topic (e.g. *"find trending Python videos"*); the agent can also open a chosen video in your default browser.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
