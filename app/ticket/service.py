from app.db.models import Ticket


def create_ticket(session, query: str, reason: str, summary: str = "", retrieved_sources: list | None = None) -> Ticket:

    ticket = Ticket(
        query = query,
        reason = reason,
        summary = summary, 
        retrieved_sources = retrieved_sources,
    )
    try:
        session.add(ticket)
        session.commit()
        session.refresh(ticket) # # Refresh reloads the object from the DB to update auto‑generated(id, timestamps etc.) or changed fields after commit.
        return ticket
    
    except Exception:
        session.rollback()
        raise