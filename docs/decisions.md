# Decisions

## 1. Pipeline logic lives outside the route
**Decision:** `answer_or_escalate(db, query, top_k)` in `app/answering/service.py` holds the whole pipeline. `routes.py` only validates input (`AskRequest`) and calls it.
**Why:**
- Eval: the golden script imports the function directly, no HTTP.
- Testing: stub the LLM or DB and assert gate behaviour; route tests only cover HTTP.
- Reuse: Streamlit, Celery or Kaarkhana can call it without FastAPI.
- Sync/async: the work is blocking (sync SQLAlchemy and OpenAI), so the route is a plain `def` and runs in FastAPI's threadpool. `async def` would block the event loop. Switching to full async later means changing the service and the route's `def`, nothing else.
**Trade-off:** one extra layer for a small app.