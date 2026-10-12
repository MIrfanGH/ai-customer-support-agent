# Architecture

Deep reference for the `/ask` pipeline. Quick overview: [README](../README.md). Why-decisions: [decisions.md](decisions.md).

Threshold and model names live in `app/config.py` / `.env`; this doc does not hard-code them except in the derivation below.



## 1. Request flow

                                    ┌─────────────────────────────────────┐
                                    │ User                                │
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
                                YES                                         NO
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
                                │                          │ error feedback (3 max-attempts) │
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


The diagram steps cover my 8-step build pipeline (classify, retrieve, tool, context, generate, validate, retry, respond): retrieve = 1, context = 2, generate = 3, validate + retry = 4, respond = 5, ticket creation = the tool call. Classify is not a separate step: the two gates are the routing (answer vs escalate). `app/llm/classifier.py` is an empty stub; a general-chat branch is not built.



## 2. Layers

| Layer | File | Responsibility |
|---|---|---|
| HTTP | `app/api/routes.py` | Validate input (`AskRequest`), call service. Plain `def`: blocking work runs in FastAPI's threadpool. |
| Application | `app/answering/service.py` | `answer_or_escalate(db, query, top_k)`: the whole pipeline. No FastAPI imports. |
| Retrieval | `app/retrieval/` | `vector_store.py` search/upsert, `context.py` context building. |
| LLM | `app/llm/` | client, prompts, tools, schemas, `llm_utils.py`, response strings in `messages.py`. |
| Tickets | `app/ticket/service.py` | `create_ticket()`: the only DB side effect besides ingestion. |
| Persistence | `app/db/` | models, session. |

The service never touches the Ticket model directly; it goes through `create_ticket()`.



## 3. Retrieval and Gate 1

- Query is embedded, ordered by cosine distance in pgvector (HNSW index).
- `score = 1 - distance`; `top_score` is returned in every response for debugging and eval.
- Gate 1 is deterministic and runs before the generation call. It saves the LLM call, not the query embedding call, which still happens (embedding is needed to get the score).

**Threshold derivation (0.35).** Picked from our own score table (`scripts/threshold_score.py`), not generic numbers: lowest in-scope query 0.369, highest out-of-scope query 0.328. The gap is 0.04 on a small query set, so treat 0.35 as provisional: it is sensitive to re-chunking, re-embedding and new queries. Re-derive it (`scripts/threshold_score.py`) after any change that moves similarity scores: chunking, embedding model, corpus, or retrieval/distance logic. Prompt changes don't affect the score. Validate on a larger labelled set that measures both false escalations and unanswerable questions that pass the gate.

**Why two gates.** Gate 1 is a cheap deterministic early exit for very weak retrieval. Gate 2 handles the case where the score looks fine but the retrieved text still doesn't answer the question; only the model reading the context can judge that.



## 4. Context building

`build_context()` labels each chunk with its source filename and appends chunks in rank order until the token budget (default 1000, tiktoken `cl100k_base`) would be exceeded. Whole chunks only. The label is what the model sees as the source name, which is why `sources_used` values come back as filenames.



## 5. Tool calling

Two tools, `tool_choice="required"`, so the model cannot answer in plain text.

| Tool | Use when | Args (Pydantic) |
|---|---|---|
| `answer_query` | context directly supports an answer (a negation that answers a yes/no or existence question counts as support) | `answer: str`, `sources_used: list[str]` |
| `escalate_to_human` | context insufficient, irrelevant or missing | `reason: str`, `summary: str` |

JSON schemas sent to the model are generated from the Pydantic models, so schema and validation can't drift.

**Grounding is mitigated, not guaranteed.** Retrieval, a context-only prompt and the escalation tool reduce unsupported answers. Pydantic checks the argument schema, not whether the answer is supported by the context.

**Application-controlled execution.** The model only requests a tool and supplies arguments. Python validates them, then runs the action. The model has no DB access and cannot execute anything.

**One LLM call on the happy path.** The classic loop (tool result goes back to the LLM for phrasing) isn't needed: for escalation the LLM already wrote `summary`, and the DB step only yields a `ticket_id` that the app attaches to the response.



## 6. Validation and retry (`call_llm_with_tools`)

                            ┌─────────────────────────────────────────┐
                            │ call LLM                                │◄───┐ max 3 attempts,
                            │ tools=[answer_query, escalate_to_human] │    │ then ValueError
                            │ tool_choice = required                  │    │
                            └─────────────────────────────────────────┘    │
                                                │                         │
                                                ▼                         │
                            ┌─────────────────────────────────────────┐    │
                            │ tool_calls present?                     ├────┤ retry
                            │ NO -> append: "You must call one        │    │
                            │ of the provided tools"  (retry)         │    │
                            └─────────────────────────────────────────┘    │
                                                │                          │
                                                ▼                          │
                            ┌─────────────────────────────────────────┐    │
                            │ json.loads(call.function.arguments)     │    │
                            └─────────────────────────────────────────┘    │
                                                │                          │
                                                ▼                         │
                            ┌─────────────────────────────────────────┐    │
                            │ Pydantic validation by tool name        ├────┘ retry: append
                            │ answer_query -> AnswerToolArgs          │      role=tool error
                            │ escalate_to_human -> EscalateToolArgs   │      (tool_call_id)
                            │ unknown tool -> invalid                 │
                            └─────────────────────────────────────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────────┐
                            │ valid -> return (tool_name, args)       │
                            └─────────────────────────────────────────┘


Errors go back as a `tool` message tied to the failing `tool_call_id`, so the model sees the error in context.

**Failure behaviour today:** after 3 failed attempts `ValueError` propagates out of `answer_or_escalate` and `/ask` returns a 500. Retries improve the odds of a valid call; they do not guarantee success. Planned: custom `LLMToolCallError`, caught in the service, which escalates with a ticket instead.

**Caveat on that fallback:** a ticket fallback only helps if ticket creation succeeds. `create_ticket` rolls back and re-raises, so a DB failure would still surface as a 500. Needs an explicit policy (log with request context, return a clear error) rather than assuming escalation always works.

**Known gap:** the code says "one tool" but only `tool_calls[0]` is used. If the model emits parallel tool calls, the extra ones get no tool response, which the OpenAI API rejects on the retry request. Planned fix: `parallel_tool_calls=False`.



## 7. Tickets

`create_ticket(session, query, reason, summary="", retrieved_sources=None)` inserts, commits, refreshes. On error it rolls back and re-raises.

- Gate 1 ticket: `reason="low retrieval confidence"`, no summary, no `retrieved_sources` (known gap).
- Gate 2 ticket: LLM's `reason` and `summary`, plus retrieved source names.



## 8. Response model

`AskResponse` covers all outcomes; fields that don't apply are `null`.

Answered:
```json
{"escalated": false, "top_score": 0.51, "answer": "...", "sources_used": ["roles"], "ticket_id": null, "message": "..."}
```
Gate 1 escalation (no `answer`):
```json
{"escalated": true, "top_score": 0.193, "answer": null, "sources_used": null, "ticket_id": 1, "message": "We couldn't find enough relevant information..."}
```
Gate 2 escalation (`answer` is the LLM's summary):
```json
{"escalated": true, "top_score": 0.531, "answer": "...", "sources_used": null, "ticket_id": 2, "message": "Your query has been escalated..."}
```

User-facing strings live in `app/llm/messages.py`, not in the service.


## 9. Ingestion

                            ┌─────────────────────────────────────┐
                            │ data/documents/*.md                 │
                            │ 7 support docs                      │
                            └─────────────────────────────────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────┐
                            │ Extraction                          │
                            │ app/ingestion/extractor.py          │
                            └─────────────────────────────────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────┐
                            │ Chunking                            │
                            │ app/ingestion/chunker.py            │
                            └─────────────────────────────────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────┐
                            │ Embeddings                          │
                            │ text-embedding-3-small (1536-dim)   │
                            └─────────────────────────────────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────┐
                            │ VectorStore.upsert()                │
                            │ ON CONFLICT (source, chunk_index)   │
                            │ DO UPDATE  -> idempotent            │
                            └─────────────────────────────────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────┐
                            │ PostgreSQL + pgvector               │
                            │ HNSW index, vector_cosine_ops       │
                            └─────────────────────────────────────┘


Run from the repo root (it reads `data/documents` by relative path):

```bash
python -m app.ingestion.pipeline
```

Needs `OPENAI_API_KEY` and a database initialised with `python -m scripts.init_db`, which runs `CREATE EXTENSION IF NOT EXISTS vector` before creating the tables (the extension must exist before the `vector` column is created).
Settings used: recursive chunker, separators `["\n\n", "\n", ". ", ""]`, chunk_size=50, overlap=10.

Idempotent: upsert on `(source, chunk_index)`, so re-running doesn't duplicate rows.
Gaps: if a file shrinks, stale higher-index chunks remain; content-hash dedup is a planned improvement.

## 10. Evaluation status

- Spec golden queries (`PROJECT_SPEC.md`): 7 (4 answerable, 2 unanswerable, 1 negative-existence).
- Earlier results on the pre-tool-calling pipeline: 5/7 passed; Q4 and Q7 failed from over-conservative refusal (`eval/full_pipeline_test_findings.md`).
- The tool-calling version has only been checked by hand on the example runs in the README. Pending: a scripted eval recording expected vs actual per query (including incorrect escalations and unsupported answers), re-run end to end after any change to chunking, embeddings, threshold, retrieval, prompts, tool schemas, model, or application logic (a prompt change can alter the answer-vs-escalate decision even though it can't change the score).


## 11. Known limitations

- Threshold 0.35 is provisional; Q7 (subscription plans) scores 0.369, close to it.
- Grounding is mitigated, not guaranteed (schema validation, not entailment).
- If ticket creation fails there is no fallback (see section 6).
- `sources_used` is model-reported and unchecked; it can cite a source the answer didn't use (Q7 cites `accounts_and_login`).
- `temperature` not pinned on the tool-calling path; `parallel_tool_calls` not disabled.
- LLM tool-call failure -> 500 (see section 6).
- Gate 1 tickets carry no retrieved sources.
- No conversation memory, reranking, hybrid search, streaming, or auth.