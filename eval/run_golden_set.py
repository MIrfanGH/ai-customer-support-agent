"""Run the golden set against the live pipeline and save per-case results.

Usage:
    python -m eval.run_golden_set            # all cases
    python -m eval.run_golden_set P05,N01    # selected case IDs

Needs the DB running and OPENAI_API_KEY set. Tickets created by escalations
are deleted at the end. Results go to eval/results/run_<timestamp>.json.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from app.answering.service import answer_or_escalate
from app.config import settings
from app.db.models import Ticket
from app.db.session import SessionLocal
from eval.grading import grade

GOLDEN_SET = Path("eval/golden_set.json")
RESULTS_DIR = Path("eval/results")
TOP_K = 5


def load_cases(argv: list[str]) -> list[dict]:
    """Load all golden cases, or only the IDs specified on the command line."""
    cases = json.loads(GOLDEN_SET.read_text(encoding="utf-8"))
    if len(argv) > 1:
        wanted = set(argv[1].split(","))
        cases = [c for c in cases if c["id"] in wanted]
    if not cases:
        # Fail loudly if an ID is misspelled; never report a misleading empty run.
        sys.exit("No matching cases")  
    return cases 


def run_case(db, case: dict) -> tuple:

    """Run one golden case and return its result row and any(or None) ticket ID to clean up."""
    # Reset per-case state so results from a previous case cannot leak into this one.
    result, gate, reason, ticket_id, outcome = None, None, None, None, "error"

    try:
        result = answer_or_escalate(db=db, query=case["query"], top_k=TOP_K)
    
    except Exception as e:
        # discard partial changes from the failed transaction so future queries can avoid error and run
        db.rollback()  
        status, detail = grade(case, "error", None, None, [], error=f"{type(e).__name__}: {e}")
    
    else:
        outcome = "escalate" if result.escalated else "answer"
        if result.escalated:
            # below threshold means retrieval blocked it (no LLM call), otherwise the LLM chose to escalate
            gate = "gate1" if result.top_score < settings.retrieval_threshold else "gate2"
        ticket_id = result.ticket_id

        if ticket_id:
            # Capture the stored reason before deleting the temporary evaluation ticket.
            reason = getattr(db.get(Ticket, ticket_id), "reason", None) 

        # Compare the actual pipeline outcome with the expected outcome and answer criteria.
        status, detail = grade(case, outcome, gate, result.answer, result.sources_used or [])

    row = {
        # Keep both the outcome and diagnostic details so failed cases can be investigated later.
        "id": case["id"], "cat": case["cat"], "query": case["query"], "expect": case["expect"],
        "outcome": outcome, "gate": gate, "status": status, "detail": detail,
        "top_score": result.top_score if result else None,
        "answer": result.answer if result else None,
        "sources_used": result.sources_used if result else None,
        "message": result.message if result else None,
        "ticket_reason": reason,
    }
    return row, ticket_id


def save_results(rows: list[dict], passed: int, total: int) -> Path:
    """Save a timestamped JSON report for comparing evaluation runs."""
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.json"

    out.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": settings.llm_model,
        # Record the threshold so results can be compared under the same retrieval settings.
        "threshold": settings.retrieval_threshold, 
        "passed": passed, "total": total, "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")  # ensure_ascii=False keeps Hinglish readable
    return out


def main() -> None:
    cases = load_cases(sys.argv)
    db = SessionLocal()
    rows, ticket_ids, passed = [], [], 0

    try:
        for case in cases:
            row, ticket_id = run_case(db, case)
            rows.append(row)
            if ticket_id:
                ticket_ids.append(ticket_id)

            # Print one compact result per case; show the answer only when grading fails.
            print(row["id"], row["status"], row["gate"], row["top_score"], row["detail"])
            if row["status"] != "pass" and row["answer"]:
                print("answer:", row["answer"][:300])  # 300 is enough to see why it failed without flooding the terminal
            if row["status"] == "pass":
                passed += 1

    finally:
        # Save the report before cleanup so a ticket-deletion failure doesn't lose the results.
        out = save_results(rows, passed, len(cases))
        try:
             # Remove only tickets created by this evaluation; don't leave test data in the DB.
            if ticket_ids:
                db.query(Ticket).filter(Ticket.id.in_(ticket_ids)).delete(synchronize_session=False)
                db.commit()
        finally:
            # Always release the database connection, even if cleanup fails.
            db.close()
        print(f"Passed cases : {passed}/{len(cases)} -> {out}")


if __name__ == "__main__":
    main()