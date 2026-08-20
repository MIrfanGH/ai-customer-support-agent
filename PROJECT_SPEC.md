# AI Customer Support Agent — Spec

## Problem
Answer customer support questions using only the approved support corpus.

## Users
Single-tenant support demo. No user accounts required for MVP.

## Must Do
- Answer questions grounded in the support corpus.
- Return source metadata for retrieved chunks.
- Refuse when no relevant context is found.
- Be idempotent on re-ingestion.

## Must NOT Do
- No refunds/payment actions.
- No modifying user data.
- No multi-tenant support.
- No conversation memory yet.
- No frontend until deployment phase.

## Golden Queries

### Answerable
1. How do I reset my password?
2. What happens if my payment fails?
3. How are user roles handled?
4. How are blog posts cached?

### Unanswerable / Refusal
5. What is your refund policy?
6. Which subscription plans are available?
7. How do I delete my account?

## Success Criteria
- Answerable queries retrieve relevant chunks.
- Answers are grounded only in retrieved context.
- Retrieved chunks contain correct source metadata.
- Unanswerable queries are refused rather than hallucinated.
- Re-ingestion does not create duplicate chunks.
