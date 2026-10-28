---
name: churn-risk-review
description: Review a customer account (usage, tickets, NPS, renewal date) and turn it into a churn risk level, the top three reasons and a save plan. Use when the user asks to assess churn risk, review an at-risk account, prepare a renewal save play or decide which accounts need attention this week.
---

# Churn risk review

Every account gets the same rubric, so a high-risk call means the same thing across the team and the save plan can be compared quarter to quarter.

## Inputs

Ask for what the user has, and mark the rest unknown:

| Field | Why it matters |
| --- | --- |
| Account name and renewal date | Sets urgency and the save window |
| Plan and contract value | Tells you whether the save is worth an executive sponsor |
| Usage trend (last 3 months, or seats active / seats bought) | The strongest early warning |
| Open and recent tickets, especially severity | Support pain that predicts non-renewal |
| NPS or CSAT score and comment | The human signal behind the numbers |
| Champion status and last contact date | A silent champion is a lost champion |
| Any competitor or budget mention | Direct evidence of a switch risk |

## Steps

1. **Normalise the inputs.** Put every metric on the same timeline: usage as a percent change over three months, tickets as count and worst severity, NPS on a -100 to 100 scale. Do not invent missing numbers; write `unknown` and say so in the output.
2. **Score the signals.** Add one risk point for each true statement:
   - Usage fell more than 10 percent over three months.
   - Fewer than half of bought seats active.
   - A severity-1 or severity-2 ticket in the last 60 days.
   - NPS of 6 or lower, or a detractor comment.
   - No champion contact in the last 30 days.
   - Renewal within 90 days with no renewal conversation logged.
   - A competitor, budget freeze or consolidation mentioned.
3. **Map the score.** 0 to 1 point = Low, 2 to 3 = Medium, 4 or more = High. If renewal is within 30 days and any usage decline exists, raise the result one level.
4. **Write the top three reasons.** Each reason must cite the specific input that produced it. No generic lines such as "engagement could be better".
5. **Build a save plan.** Three to five actions, each with an owner role and a date inside the renewal window. Start with the cheapest high-leverage action (a champion call, not a discount).
6. **State what would change the verdict.** Name the signal to watch and the threshold that would move the account one level in either direction.

## Output format

```text
Account: Acme GmbH
Renewal: 2026-12-15 (47 days)
Risk: High (5 points)

Reasons
1. Seats active fell from 82 to 39 (-52 percent) over three months.
2. Two severity-2 tickets in the last 30 days, both unresolved.
3. No champion contact since 2026-09-02 (86 days).

Save plan
- [ ] Customer Success lead: call the champion by 2026-11-05, confirm the renewal owner.
- [ ] Support lead: close both severity-2 tickets by 2026-11-08 and send a written summary.
- [ ] Account executive: bring a right-sized plan option to the 2026-11-20 review.

Watch: any usage recovery above 60 active seats by 2026-11-20 moves this to Medium.
Unknown: contract value, competitor mentions.
```

## Rules

- Use only the data the user supplied. Missing data is `unknown`, never zero and never a guess.
- Every reason quotes a number, date or exact comment from the input.
- Never promise a discount, credit or contract term the user did not authorise.
- Keep names and figures exactly as given; do not round a date to a different month.
- If the user has no usage data at all, say the risk call is provisional and list the two inputs that would change it most.

Credits: zeebyx/operator-skills contributors
