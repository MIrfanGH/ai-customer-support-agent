## Day 5 — Initial Golden Query Findings
(temp file — will be consolidated into a permanent findings doc after proper/full evaluation)

- Q1 "How do I reset my password?" — Passed.
- Q2 "What happens if my payment fails?" — Passed.
- Q3 "How are user roles handled?" — Passed.
- Q4 "How are blog posts cached?" — Failed. posts.md was retrieved
  (confirmed in sources_used), but the model refused, citing lack of
  "specific mechanisms." Generation-layer over-conservatism, not a
  retrieval gap — corpus already answers this at the behavioral level.
- Q5 "What is your refund policy?" — Passed, correctly refused.
- Q6 "How do I delete my account?" — Passed, correctly refused.
- Q7 "Which subscription plans are available?" — Failed. Confirmed via
  raw search() debug: donations.md ranked #1 and contained the exact
  answer ("not subscriptions"). Model still refused with empty
  sources_used. Root cause: model doesn't treat a negation as sufficient
  grounds to answer a non-existence question.
- Source formatting: sources_used inconsistent ("donations" vs "Source:
  donations") — cosmetic, from context label bleeding into model output.
  Fix during Day 7 cleanup, not blocking.

### Current assessment
Core pipeline (retrieve → context → generate → validate → respond) is
mechanically sound — 5/7 pass, 0 crashes. 
Q4 and Q7 share one root cause: the model's refusal threshold is too strict for
partial-coverage and negative-existence questions. Candidate fix:
explicit prompt instruction that negation/absence statements count as
sufficient grounding. Defer implementation to evaluation time — re-test against
full eval set before tuning further, to avoid overfitting the prompt to
2 known cases.