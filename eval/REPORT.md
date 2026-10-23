# Eval Report

## What I tested
- 41 golden cases in `golden_set.json`: direct 16, uncovered 7, paraphrase 5, negation 4, multi-chunk 3, off-topic 3, adversarial 3. 28 should be answered and 13 should be escalated.
- Setup: gpt-4o-mini, temperature=0, Gate 1 threshold 0.35, top_k=5.
- `grading.py` checks the outcome, the gate, required and forbidden phrases, and the cited sources.
- To run it: `python -m eval.run_golden_set [ID,ID]` the ID is if running specific ID/s only. 
   Results are saved in `results/`.

## Baseline: 37/41
Saved in `results/baseline.json` (2026-10-18).

| Category | Pass |
|---|---|
| direct | 16/16 |
| multi-chunk | 3/3 |
| off-topic | 3/3 |
| adversarial | 3/3 |
| uncovered | 6/7 |
| paraphrase | 4/5 |
| negation | 2/4 |

## The failures

| Case | Label | Where it broke | What happened |
|---|---|---|---|
| P05 | false_escalation_gate1 | Retrieval | Hinglish query. The top two chunks were the right password-reset ones, but top_score was 0.349, just under 0.35, so Gate 1 blocked it |
| N01 | false_escalation_gate2 | Generation | The right chunk was rank 1 and in the context ("Donations are not subscriptions"), but the LLM still escalated. The golden set expects "no subscription plans are documented". That is my call, since the corpus is the whole knowledge base |
| N04 | bad_citation | Citations | The LLM put context labels and chunk text into `sources_used` |
| U07 | false_answer | Generation | The retrieved chunk is on topic (0.68) but never names a provider. The LLM answered a nearby question instead |
| A02 (passed) | fragile | Retrieval | Escalated at Gate 1 by only 0.007, with flat scores (0.343 to 0.328). This is luck, not proof the threshold protects against adversarial input |

## What I found
1. **The LLM controls the citations.** 15 of 41 cases have malformed `sources_used` (label or chunk text leaking in). 13 of them pass only because the grader cleans the strings up.
2. **The answer/refuse line is wrong in both directions.** N01 refuses something the golden set treats as answerable, and U07 answers something the docs don't cover. One rule should cover both: the context must directly answer the question, "X is not offered" counts as an answer, and being on topic alone does not.
3. **A single score cutoff is brittle.** An answerable query (P05, 0.349) and an unanswerable one (A02, 0.343) land in the same 0.34 to 0.37 band, so lowering the threshold to save P05 would break A02. Non-English queries also score lower.

## What I'll fix, in order
One change per run, then re-run all 41 and compare to the baseline.
1. Take `sources_used` from the retrieved chunk metadata instead of the LLM output.
2. Add the sufficiency rule to the tool prompt, with one example for negation and one for off-question.
3. For P05, try rewriting the query to English first. If that doesn't work, document it as a known limitation.

I'm not lowering the threshold.

## Checked
- The DB content matches the source files (55 chunks, no leftovers), so the baseline scores are valid.

## Still open
- Debug-script scores differ from the run for P05 (0.310 vs 0.349), U07 (0.684 vs 0.700) and N04 (0.408 vs 0.397). N01 and A02 match exactly. I haven't found the cause yet.

## After deploy
- Chunks split mid-sentence and leave headings orphaned, so heading-aware chunking is worth trying.
- Hybrid search (BM25) may help P05.
- A bigger eval set to calibrate the threshold properly.