"""Pure grading logic (no app imports) so it can be unit-tested."""
from pathlib import Path

PASS = "pass"
FALSE_ESC_G1 = "false_escalation_gate1"   # answerable, blocked by retrieval threshold
FALSE_ESC_G2 = "false_escalation_gate2"   # answerable, LLM refused (over-conservative)
FALSE_ANSWER = "false_answer"             # unanswerable, bot answered anyway (hallucination risk)
WRONG_CONTENT = "wrong_content"           # right outcome, answer text fails keyword checks
BAD_CITATION = "bad_citation"             # answer ok, cited sources wrong/empty
ERROR = "error"



def norm_source(s: str) -> str:
    """
    Normalize a source string by removing any leading or trailing whitespace, stripping square brackets, 
    and removing the "Source:" prefix if present. It then returns the stem(filename without its extension) of the path
    """
    s = s.strip().strip("[]").strip()
    if s.lower().startswith("source:"):
        s = s[len("source:"):]
    return Path(s.strip()).stem



def check_content(text: str | None, q: dict) -> tuple[list, list]:
    """
    Check that the text contains all required keywords and does not contain any forbidden keywords.
    Returns two lists: missing keywords and forbidden keywords found in the text."""
    t = (text or "").lower()
    missing = [g for g in q.get("must_include", []) if not any(a.lower() in t for a in g)]
    forbidden = [f for f in q.get("must_not", []) if f.lower() in t]
    return missing, forbidden


def grade(q: dict, outcome: str, gate: str | None, text: str | None,
          cited: list[str], error: str | None = None) -> tuple[str, str]:
    
    """
    This fucntion grades the outcome of a query based on the expected outcome and the actual outcome. 
    It checks if the outcome matches the expected-outcome, and if not, it returns an appropriate error code. 
    It also checks the content of the answer for required and forbidden keywords, and checks the cited sources against the expected sources. 
    
    Returns: a tuple containing a status code and a detail message.
    q:dict -> the query dictionary containing the expected outcome and other grading criteria not just the query string.
    """
    if outcome == "error":
        return ERROR, error or ""
    if q["expect"] == "answer":
        if outcome == "escalate":
            return (FALSE_ESC_G1 if gate == "gate1" else FALSE_ESC_G2), ""
        missing, forbidden = check_content(text, q)
        if missing or forbidden:
            return WRONG_CONTENT, f"missing={missing} forbidden={forbidden}"
        want = set(q.get("sources_any", []))
        got = {norm_source(c) for c in cited}
        if want and not (want & got):
            return BAD_CITATION, f"cited={sorted(got)} want_any={sorted(want)}"
        return PASS, ""
    # expect escalate
    if q["expect"] == "escalate":
        if outcome == "answer":
            return FALSE_ANSWER, ""
        _, forbidden = check_content(text, q)  #  '_'  used to ignore the first return value (missing keywords) since we only care about forbidden keywords in this case.
        if forbidden:
            return WRONG_CONTENT, f"forbidden={forbidden}"
        return PASS, ""
