# MIT CampusOS chatbot

This backend implements a grounded chatbot over the documents in
`../minor_project_docs`. It combines local dense retrieval, BM25 keyword
retrieval, optional scanned-page visual retrieval, and one configurable answer
provider. Retrieved evidence is kept separate from instructions, every answer
can return page-aware citations, and unsupported questions fall back to a
clear no-evidence response.

## Pipeline

1. `app.rag.ingest` extracts PDF pages and CSV rows, chunks text, records source
   metadata, and builds the local text index.
2. `app.rag.hybrid` fuses dense and BM25 results. When visual RAG is enabled it
   also searches rendered scanned pages with `vidore/colSmol-500M`.
3. `app.routers.chat_router` filters irrelevant results and combines official
   document evidence with any matching community evidence.
4. The selected provider receives only the question, recent history, numbered
   evidence, and relevant page images.
5. `app.answer_verifier` validates citation markers. The response exposes the
   provider, model, confidence, verification warnings, and citation locations.

## Quick start

Run these commands from `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

For the tested Gemini configuration, set these values in `.env` and insert your
own key. Never commit `.env`.

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-flash-lite-latest
GEMINI_EMBEDDINGS_ENABLED=false
VISUAL_RAG_ENABLED=false
```

Other supported generation providers are OpenAI and Anthropic:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

```dotenv
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5
```

`LLM_PROVIDER=auto` selects the first configured provider in this order:
OpenAI, Anthropic, Gemini, then the local extractive fallback.

## Build the RAG index

```powershell
python -m app.rag.ingest
```

The generated files live under `backend/data/` and are intentionally ignored
by Git. Re-run ingestion after adding or changing source documents.

Answer generation and text embeddings are independent settings. Keep
`GEMINI_EMBEDDINGS_ENABLED=false` when using the default local index. If you
turn it on or change `EMBEDDING_MODEL`, rebuild the entire index before testing.

## Optional visual RAG for scanned PDFs

Visual retrieval is opt-in because its first setup downloads model weights and
uses significantly more memory than text retrieval.

```dotenv
VISUAL_RAG_ENABLED=true
VISUAL_RAG_SCOPE=scanned
COLVISION_MODEL=vidore/colSmol-500M
COLVISION_DEVICE=auto
COLVISION_LOCAL_FILES_ONLY=false
```

Then prefetch the model and rebuild the index:

```powershell
python -m app.rag.prefetch_visual_model
python -m app.rag.ingest
```

`COLVISION_DEVICE=auto` uses CUDA when available and otherwise uses the CPU.
Use `VISUAL_RAG_SCOPE=all` only if every PDF page needs a visual embedding;
`scanned` is substantially lighter.

## Run and test

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Useful endpoints:

- Health and provider state: `GET http://127.0.0.1:8080/api/health`
- Interactive API docs: `http://127.0.0.1:8080/docs`
- Chat: `POST http://127.0.0.1:8080/api/chat`

Example request body:

```json
{
  "message": "What is the minimum attendance requirement?",
  "role": "student",
  "language": "en",
  "session_id": "manual-test-1"
}
```

Run the fast test suite without downloading visual model weights:

```powershell
python -m pytest tests/test_rag_pipeline.py -q
```

Run the retrieval fixture evaluation after the index is built:

```powershell
python -m app.rag.evaluate
```

## Expected behavior

- An answer grounded in indexed evidence includes `[E1]`, `[E2]`, and similar
  inline markers plus structured citations in the API response.
- Questions outside the indexed corpus return a no-evidence response instead
  of a fabricated answer.
- If the configured remote provider fails, the request uses the local
  evidence-only provider rather than returning an ungrounded answer.
- A citation with a PDF page can be opened through
  `/api/search/page/{document_id}/{page_number}`.
