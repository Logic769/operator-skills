---
name: icp-lead-scoring
description: Score and tier a list of leads or accounts against an ideal customer profile (ICP), with a short reason for each score. Use when the user asks to score, rank, qualify, prioritize or tier leads, accounts or prospects.
---

# ICP lead scoring

Scores are only useful if they are consistent and explainable. This skill forces a written rubric first, then applies it the same way to every row.

## Steps

1. **Get or build the rubric.** If the user has an ICP, use it. If not, ask for these and nothing more:
   - Who buys (titles or functions)
   - Company size range
   - Industries in and out
   - Regions served
   - One or two buying signals (hiring for a role, using a tool, recent funding)

2. **Write the rubric back** as a table before scoring, and get a yes:

   | Criterion | Weight | Full points when | Zero when |
   |---|---|---|---|
   | Buyer title | 30 | Head/VP/Director of Ops, RevOps, CS | Intern, student, unrelated function |
   | Company size | 25 | 20 to 500 employees | Under 5 or over 5,000 |
   | Industry | 20 | B2B SaaS, agencies, services | Government, education |
   | Region | 10 | Target regions | Outside service area |
   | Signal | 15 | Signal present and dated in last 90 days | No evidence |

   Weights must sum to 100.

3. **Score every row** on each criterion. Award partial points only by the rule in the table. If data is missing, score zero for that criterion and say "missing", never guess.

4. **Tier:** A = 75 to 100, B = 50 to 74, C = 25 to 49, D = under 25.

5. **For lists over about 50 rows**, write a small script that applies the rubric for the structured columns (size, region, industry) and use judgment only for titles and signals. Same rubric, same answer every time.

## Output format

Add columns `icp_score`, `icp_tier`, `icp_reason` to the user's sheet. The reason is one line naming the biggest plus and the biggest minus:

```
icp_score: 82 | icp_tier: A | icp_reason: VP Ops at 120-person SaaS; no recent signal found
```

Then summarize: count per tier, the five best A leads, and which missing field cost the most points across the list (so the user knows what to enrich).

## Rules

- Never change the rubric mid-list. If it looks wrong, stop and propose a revision.
- Do not invent firmographics. Missing is missing.
