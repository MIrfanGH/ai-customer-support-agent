# AI Customer Support Agent

**A RAG-based support agent that answers from an approved docs corpus, and hands off to a human ticket when it can't answer confidently.**

> Single-tenant. Built end-to-end: ingestion, retrieval, tool-calling, validation/retry, ticketing, API.


##  What This Is

A FastAPI service that takes a customer question, searches a support knowledge base with vector search, and either returns a grounded answer or creates a support ticket. It is instructed to answer only from the retrieved context, and weak evidence is escalated rather than guessed. This reduces unsupported answers; it is not a formal guarantee (see Known Limitations).

The demo corpus is the product documentation of my own SaaS, [MyDailyBlog](https://github.com/MIrfanGH/Django_Blog): 7 markdown files (accounts and login, AI summaries, donations, email notifications, posts, roles, troubleshooting), 55 chunks.

---

##  Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Pydantic v2, Uvicorn |
| Database | PostgreSQL + pgvector (HNSW index, cosine) via SQLAlchemy |
| Embeddings | OpenAI `text-embedding-3-small` (1536-dim) |
| LLM | OpenAI `gpt-4o-mini`, tool calling |
| Chunk budgeting | tiktoken (`cl100k_base`) |
| Local infra | Docker (`pgvector-db`) |

---

## 🔧 Production Problems Addressed

| Problem | Engineering Approach |
|---|---|
| Unsupported answers on weak evidence | Gate 1: retrieval score below threshold skips LLM generation and creates a ticket (the query is still embedded) |
| Model drifting outside the docs | Context-only prompt + forced tool call with an `escalate_to_human` exit (a mitigation, not a guarantee) |
| Malformed LLM output | Pydantic validation + retry with error feedback (max 3) |
| Unanswerable questions lost | Every escalation becomes a ticket; metadata varies by path (Gate 1 retrieved-source capture is a known gap) |
| Threshold guesswork | 0.35 chosen from this corpus's own scores; provisional. The 41-case eval shows answerable and unanswerable queries overlapping in the 0.34-0.37 band (see Evaluation) |
| Duplicate chunks on re-ingest | Idempotent upsert on `(source, chunk_index)` |
| Untestable pipeline | HTTP-free `answer_or_escalate()`; route is a thin wrapper |
| Blocking calls in an async server | Plain `def` route, runs in FastAPI's threadpool |

---

##  Key Features

-  **RAG** over pgvector with similarity scores returned on every response (`top_score`)
-  **Two escalation gates**: Gate 1 deterministic (retrieval score, before the LLM), Gate 2 the LLM's own decision (`escalate_to_human`)
-  **Forced tool calling**: the model must call `answer_query` or `escalate_to_human` (`tool_choice=required`), never free text; the first call is used (parallel calls not yet disabled)
-  **Validated + retried**: tool arguments checked with Pydantic (schema, not factual support), bad calls fed back to the model
-  **Ticketing**: every escalation is persisted as a ticket (query, reason). Gate 2 tickets also store the LLM's summary and retrieved sources; Gate 1 tickets don't yet (known gap)
-  **One LLM call on the happy path**: tool arguments are the final content, no second phrasing call

---

##  Architecture (Quick View)


                                      ┌─────────────────────────────────────┐
                                      │                 User                │
                                      └─────────────────────────────────────┘
                                                          │
                                                          ▼
                                      ┌─────────────────────────────────────┐
                                      │ POST /ask   {query, top_k}          │
                                      │ AskRequest validation               │
                                      └─────────────────────────────────────┘
                                                          │
                                                          ▼
                                      ┌─────────────────────────────────────┐
                                      │ answer_or_escalate()                │
                                      │ app/answering/service.py            │
                                      └─────────────────────────────────────┘
                                                          │
                                                          ▼
                                      ┌─────────────────────────────────────┐
                                      │ 1. RETRIEVE                         │
                                      │ VectorStore.search()                │
                                      │ pgvector cosine similarity          │
                                      │ -> top-K chunks + scores            │
                                      └─────────────────────────────────────┘
                                                          ▼
                                                top_score < 0.35 ?
                                    ┌─────────────────────┴─────────────────────┐
                                   YES                                           NO
                                    ▼                                           ▼
                      ┌─────────────────────────┐             ┌─────────────────────────────────┐
                      │ GATE 1                  │             │ 2. BUILD CONTEXT                │
                      │ low retrieval confidence│             │ build_context(): labeled,       │
                      └─────────────────────────┘             │ token-bounded chunks            │
                                    │                          └─────────────────────────────────┘
                                    ▼                                           │
                      ┌─────────────────────────┐                              ▼
                      │ create_ticket()         │             ┌─────────────────────────────────┐
                      │ reason: low retrieval   │             │ 3. GENERATE                     │
                      │ confidence              │             │ LLM + 2 tools,                  │
                      │ NO generation call      │             │ tool_choice = required          │
                      └─────────────────────────┘             └─────────────────────────────────┘
                                    │                                           │
                                    │                                           ▼
                                    │                          ┌─────────────────────────────────┐
                                    │                          │ 4. VALIDATE (Pydantic)          │
                                    │                          │ invalid -> RETRY with           │
                                    │                          │ error feedback (max 3)          │
                                    │                          └─────────────────────────────────┘
                                    │                                           │
                                    │                                           ▼
                                    │                          ┌─────────────────────────────────┐
                                    │                          │ tool chosen by the LLM:         │
                                    │                          │ answer_query                    │
                                    │                          │   -> grounded answer            │
                                    │                          │ escalate_to_human               │
                                    │                          │   -> GATE 2 -> create_ticket()  │
                                    │                          └─────────────────────────────────┘
                                    └─────────────────────┬─────────────────────┘
                                                          │
                                                          ▼
                                      ┌─────────────────────────────────────┐
                                      │ 5. RESPOND                          │
                                      │ AskResponse                         │
                                      │ (answer | ticket_id)                │
                                      └─────────────────────────────────────┘


There is no separate classify step: the two gates are the routing between answering and escalating.

---

##  Example Runs

`top_score` is cosine similarity (1 = identical) of the best-matching chunk. Gate 1 threshold is 0.35. These are illustrative runs. The scripted evaluation (41 cases, expected vs actual) is in [`eval/REPORT.md`](eval/REPORT.md).

| Example query | What it tests | top_score | Path | Result |
|---|---|---|---|---|
| "Can you book me a flight?" | Completely out of scope | 0.193 | Gate 1 | Escalated, no generation call |
| "Can I get a refund for my donation?" | Related doc exists (`donations`), but no refund policy | 0.531 | Gate 2 | Escalated by the LLM |
| "How are user roles handled?" | In scope | 0.51 | Gate 2 | Answered from `roles` |

---

##  Project Structure

```
ai-customer-support-agent/
├── app/
│   ├── main.py              FastAPI app
│   ├── config.py            settings from .env
│   ├── api/routes.py        POST /ask
│   ├── answering/service.py answer_or_escalate() - the pipeline
│   ├── llm/                 client, prompts, tools, schemas, messages, llm_utils
│   ├── retrieval/           vector_store, context
│   ├── ingestion/           extractor, chunker, embedder, pipeline
│   ├── ticket/service.py    create_ticket()
│   └── db/                  models, session
├── data/documents/          source markdown
├── scripts/                 init_db, threshold_score, debug_pipeline
├── eval/                    golden_set.json, grading.py, run_golden_set.py, results/baseline.json, REPORT.md
├── docs/                    architecture.md, decisions.md
├── PROJECT_SPEC.md
└── COSTS.md
```

---

##  Quick Start (Local)

```bash
git clone https://github.com/MIrfanGH/ai-customer-support-agent.git && cd ai-customer-support-agent
python -m venv venv

# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

**1. PostgreSQL + pgvector** (Docker, host port 5433):

```bash
docker run -d --name pgvector-db -p 5433:5432 \
  -e POSTGRES_USER=llm_user \
  -e POSTGRES_PASSWORD=change_me \
  -e POSTGRES_DB=customer_support_agent \
  pgvector/pgvector:pg16
```


**2. `.env`** (repo root; use the same password as above, and a real one outside local dev):

```env
DATABASE_URL=postgresql://llm_user:change_me@localhost:5433/customer_support_agent
OPENAI_API_KEY=your-openai-api-key
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
RETRIEVAL_THRESHOLD=0.35
```


**3. Create tables, ingest, run** (from the repo root):

```bash
python -m scripts.init_db            # enables pgvector extension, then creates doc_chunks + tickets tables
python -m app.ingestion.pipeline     # ingests data/documents/*.md (needs OPENAI_API_KEY)
uvicorn app.main:app --reload        # docs at http://127.0.0.1:8000/docs
```

Re-running ingestion is safe (idempotent upsert). `init_db` needs a DB user allowed to create the `vector` extension (the Docker user above is; on managed Postgres such as RDS, check that `vector` is available and permitted).

---


##  Try It

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "How are user roles handled?", "top_k": 5}'
```

```json
{
  "escalated": false,
  "top_score": 0.51,
  "answer": "...",
  "sources_used": ["roles"],
  "ticket_id": null,
  "message": "..."
}
```

Escalated responses return `"escalated": true` and a `ticket_id`. Full response shapes: [docs/architecture.md](docs/architecture.md#8-response-model).

---

##  Evaluation

A scripted golden eval (`eval/golden_set.json`, 41 cases: direct, paraphrase, multi-chunk, negation, unanswerable, off-topic, adversarial) checks the outcome (answer vs escalate), the gate, required and forbidden phrases, and whether the cited sources include an expected document (format-normalized; citations are not verified against the retrieved chunks). `temperature=0`.

```bash
python -m eval.run_golden_set              # all cases
python -m eval.run_golden_set P05,N01      # selected cases
```

Needs the DB running and `OPENAI_API_KEY`. Results are written to `eval/results/run_<timestamp>.json`; the runner deletes the tickets it creates.

**Baseline: 37/41** (`eval/results/baseline.json`). Failures: a Hinglish query blocked by Gate 1 (P05), a negation question over-escalated by the LLM (N01), an off-question answer (U07), and a citation leaking chunk text (N04). Diagnosis, failure modes and the fix plan are in [`eval/REPORT.md`](eval/REPORT.md).

---

##  Known Limitations

- **Threshold is provisional.** 0.35 is a single absolute-cosine cutoff, and the eval shows it cannot cleanly separate the classes: an answerable Hinglish query scores 0.349 (falsely escalated, P05) while an adversarial query is escalated at Gate 1 by only 0.007 (A02, 0.343). That pass is luck, not protection: the threshold is a relevance filter, not a security control.
- **Grounding is mitigated, not guaranteed.** Pydantic validates the output schema, not factual support from the context. The eval found an off-question answer (U07: the retrieved chunk is on-topic but names no AI provider) and a refusal of a negation question (N01: the docs say donations are not subscriptions, which the golden set treats as sufficient to answer "no subscription plans documented").
- **`sources_used` is model-reported and unverified.** The eval shows the model copying context labels and chunk text into it (15 of 41 cases carry malformed sources; the grader normalizes most). Planned fix: derive sources from retrieved chunk metadata.
- **Non-English queries** score lower against the English-only corpus.
- If the LLM fails to produce a valid tool call after 3 attempts, `/ask` returns a 500 (planned: escalate with a ticket). If ticket creation also fails there is no fallback yet.
- Gate 1 tickets do not store retrieved sources.
- No conversation memory, reranking, hybrid search, or streaming YET.

---

##  Deep Documentation

Per-step walkthrough, tool-calling and retry flow, failure behaviour, threshold derivation, ingestion: [`docs/architecture.md`](docs/architecture.md). Design decisions: [`docs/decisions.md`](docs/decisions.md).

---

## 👤 Author

**Muhammad Irfan** - Python Backend & AI Application Engineer | FastAPI, Django, RAG, pgvector, AWS, Celery

[github.com/MIrfanGH](https://github.com/MIrfanGH) · [LinkedIn](https://www.linkedin.com/in/muhammad-irfan891) · Mumbai, India