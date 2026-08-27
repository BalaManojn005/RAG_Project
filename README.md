# RAG Project

Local document question-answering app with FastAPI, React, FAISS, and Ollama.

## Requirements

- Python 3.11 or later
- Node.js 20 or later
- [Ollama](https://ollama.com/) running locally, with the configured model:

  ```powershell
  ollama pull gemma3:4b
  ```

## Run locally

From the project root, create and activate a virtual environment, then install
the backend dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the frontend URL Vite prints (normally `http://localhost:5173`). The
frontend connects to `http://127.0.0.1:8000` by default. To use another API
address, set `VITE_API_URL` before starting Vite.

## Checks

```powershell
py -m pytest
cd frontend; npm run lint; npm run build
```

Upload a PDF before asking document questions. HTS questions use the included
HTS index; all answers still require Ollama to be available.
