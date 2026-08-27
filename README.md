# RAG Project — AI Document Assistant

A local **Retrieval-Augmented Generation (RAG) document assistant** that lets users upload PDF documents, ask questions in natural language, receive grounded answers, see retrieved source chunks, and continue conversations through chat history.

The project combines **React + Vite** on the frontend with **FastAPI** on the backend. Documents are processed into chunks, converted into embeddings, indexed with **FAISS**, searched with **BM25**, and combined using **Reciprocal Rank Fusion (RRF)** before the relevant context is sent to **Ollama / Gemma 3 4B** for answer generation.

## Features

- PDF upload and text extraction
- Text cleaning and document chunking
- Semantic embeddings using `all-MiniLM-L6-v2`
- Dense vector retrieval with FAISS
- Keyword retrieval with BM25
- Hybrid retrieval using Reciprocal Rank Fusion (RRF)
- Grounded LLM responses using Ollama and `gemma3:4b`
- True token-by-token streaming with Server-Sent Events (SSE)
- Retrieved source chunks returned with answers
- Conversation creation and persistent chat history
- Open and delete previous conversations
- HTS-related question handling through the included HTS index
- Backend smoke tests with pytest
- Frontend linting and production build checks

## Architecture

```text
                    React + Vite
                         |
                    REST / SSE
                         |
                    FastAPI API
                         |
             +-----------+-----------+
             |                       |
         PDF Upload                Chat
             |                       |
       Text Extraction         Question Processing
             |                       |
          Cleaning                    |
             |                       |
          Chunking                    |
             |                       |
         Embeddings                   |
             |                       |
             v                       v
          FAISS <-------------> BM25
             |                       |
             +-----------+-----------+
                         |
                        RRF
                         |
                  Top Relevant Chunks
                         |
                    Document Context
                         |
                  Ollama / Gemma 3 4B
                         |
                  Grounded Answer
                         |
              +----------+----------+
              |                     |
            Tokens                Sources
              |                     |
              +----------+----------+
                         |
                    React UI
```

## How the RAG pipeline works

1. **Upload** — the user uploads a PDF through the React interface.
2. **Extract** — the backend extracts readable text from the PDF.
3. **Clean** — extracted text is normalized before indexing.
4. **Chunk** — the document is divided into smaller chunks for retrieval.
5. **Embed** — chunks are converted into vectors using `all-MiniLM-L6-v2`.
6. **Index** — vectors are stored in a local FAISS index and text is prepared for BM25 retrieval.
7. **Retrieve** — a question is searched using both semantic FAISS retrieval and keyword BM25 retrieval.
8. **Fuse** — RRF combines the two rankings into a final hybrid ranking.
9. **Generate** — the top relevant document context is supplied to Ollama / Gemma 3 4B.
10. **Ground** — the LLM is instructed to answer only from the supplied document context and avoid inventing information.
11. **Stream** — the answer can be sent to the frontend progressively using SSE.
12. **History** — user and assistant messages, including sources for assistant responses, are stored as conversation history.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React 19 + Vite |
| Backend | FastAPI + Uvicorn |
| Language | Python |
| PDF processing | PyMuPDF |
| Embeddings | Sentence Transformers |
| Embedding model | `all-MiniLM-L6-v2` |
| Dense retrieval | FAISS CPU |
| Sparse retrieval | BM25 |
| Hybrid ranking | Reciprocal Rank Fusion (RRF) |
| LLM runtime | Ollama |
| LLM model | `gemma3:4b` |
| Streaming | Server-Sent Events (SSE) |
| History | Local JSON storage |
| Testing | Pytest |

## Requirements

Install these before running the project:

- Python 3.11 or later
- Node.js 20 or later
- npm
- Ollama
- Git

The backend dependencies are pinned in `backend/requirements.txt`.

## Clone the repository

```powershell
git clone https://github.com/BalaManojn005/RAG_Project.git
cd RAG_Project
```

Make sure you are using the `main` branch:

```powershell
git checkout main
git pull origin main
```

## 1. Set up the backend

From the project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

### If PowerShell blocks virtual-environment activation

You can run the environment directly without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

## 2. Install and prepare Ollama

Install Ollama on the system and make sure the Ollama service is running.

Pull the configured model:

```powershell
ollama pull gemma3:4b
```

Optional verification:

```powershell
ollama list
```

You should see `gemma3:4b` in the installed models.

## 3. Start the backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

The API should be available at:

```text
http://127.0.0.1:8001
```

FastAPI documentation:

```text
http://127.0.0.1:8001/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8001/openapi.json
```

Keep this terminal running.

## 4. Set up the frontend

Open a **second terminal** and run:

```powershell
cd RAG_Project\frontend
npm install
npm run dev
```

Vite will print the frontend URL, normally:

```text
http://localhost:5173
```

Open that URL in a browser.

The frontend is configured to use the backend at:

```text
http://127.0.0.1:8001
```

If another API address is required, set `VITE_API_URL` before starting Vite. For example:

```powershell
$env:VITE_API_URL="http://127.0.0.1:8001"
npm run dev
```

## 5. Use the application

### First run

1. Start Ollama.
2. Start the FastAPI backend on port `8001`.
3. Start the React frontend.
4. Open the Vite URL in your browser.
5. Upload a **text-based PDF**.
6. Wait for the upload/indexing operation to finish.
7. Ask a question about the document.
8. Verify the answer, streaming output, and retrieved sources.
9. Ask a follow-up question to test conversation context.
10. Open chat history to verify the saved conversation.

### Important

The current document pipeline expects PDFs with readable text. Scanned/image-only PDFs require OCR support, which is not included in the current pipeline.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/upload` | Upload a PDF and build its local index |
| POST | `/chat` | Generate a normal grounded answer |
| POST | `/chat/stream` | Stream a grounded answer using SSE |
| GET | `/history` | Return saved conversations |
| GET | `/history/{conversation_id}` | Return one conversation |
| DELETE | `/history/{conversation_id}` | Delete one conversation |

## Testing and verification

### Backend syntax checks

From the project root:

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\main.py
.\.venv\Scripts\python.exe -m py_compile backend\api\chat.py
.\.venv\Scripts\python.exe -m py_compile backend\api\upload.py
.\.venv\Scripts\python.exe -m py_compile backend\rag\rag_pipeline.py
.\.venv\Scripts\python.exe -m py_compile backend\llm\llm_client.py
.\.venv\Scripts\python.exe -m py_compile backend\retrieval\hybrid_retriever.py
```

### Run pytest

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Frontend checks

```powershell
cd frontend
npm run lint
npm run build
```

## Quick backend API test

PowerShell's `curl` command can map to `Invoke-WebRequest`. To use the real curl executable, use `curl.exe`.

Check the API:

```powershell
curl.exe http://127.0.0.1:8001/openapi.json
```

Test `/chat` without relying on curl JSON quoting:

```powershell
$body = @{ question = "What is this document about?" } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "http://127.0.0.1:8001/chat" -Method Post -ContentType "application/json" -Body $body
```

Test the streaming endpoint:

```powershell
$body = @{ question = "What is this document about?" } | ConvertTo-Json -Compress
curl.exe -N -X POST "http://127.0.0.1:8001/chat/stream" -H "Content-Type: application/json" --data-raw $body
```

A successful streaming response contains events such as:

```text
event: conversation
event: token
event: sources
event: done
```

## Project data and generated files

Document indexes and generated local data are not intended to be committed to Git. They are created locally when documents are processed.

Typical generated data includes:

```text
data/history/
backend/storage/data/
```

The `.gitignore` prevents generated artifacts, virtual environments, caches, and secrets from being committed.

## Troubleshooting

### Backend does not start

Check whether port `8001` is already in use:

```powershell
netstat -ano | findstr :8001
```

If an old Python/Uvicorn process is using the port, stop that process using its actual PID:

```powershell
taskkill /PID <PID> /F
```

Then start the backend again.

### Ollama/model error

Check Ollama:

```powershell
ollama list
```

If `gemma3:4b` is missing:

```powershell
ollama pull gemma3:4b
```

### Frontend cannot connect to backend

Confirm the backend is running:

```text
http://127.0.0.1:8001/openapi.json
```

Then make sure the frontend uses:

```text
VITE_API_URL=http://127.0.0.1:8001
```

### PowerShell curl error

Use `curl.exe` instead of `curl` when you specifically want the curl program:

```powershell
curl.exe http://127.0.0.1:8001/openapi.json
```

For JSON POST requests, `Invoke-RestMethod` is often easier in PowerShell.

## Review / Demo Checklist

Before a project demonstration:

- [ ] Ollama is running
- [ ] `gemma3:4b` is installed
- [ ] Backend starts on port `8001`
- [ ] `/docs` opens successfully
- [ ] Frontend starts successfully
- [ ] A text-based PDF can be uploaded
- [ ] Document indexing completes
- [ ] A document question returns a grounded answer
- [ ] Streaming displays tokens progressively
- [ ] Sources are displayed/returned
- [ ] An unsupported question produces the document-grounding fallback
- [ ] Follow-up questions use conversation history
- [ ] History can be opened
- [ ] Conversations can be deleted
- [ ] Backend tests pass
- [ ] Frontend lint and build pass

## Notes

This is a **local RAG application**. The LLM runs through Ollama on the local machine, so an external hosted LLM API key is not required for the configured generation path.

For best demonstration results, use a clean text-based PDF containing information that can be clearly verified from the source document.

## License

This project is provided for academic/project demonstration purposes.
