---
name: weekly-ops-report
description: Build a one-page weekly status report for a team, project or client with RAG status, metrics against target, risks and decisions needed. Use when the user asks for a weekly update, status report, progress report, client update or leadership summary.
---

# Weekly ops report

A status report exists to get decisions made. Lead with what needs attention, not with a list of activities.

## Inputs

Use whatever the user provides: task tracker exports, notes, metrics, last week's report. If last week's report exists, compare against it.

## Steps

1. **Pick 3 to 5 metrics** that the reader cares about. Show this week, last week and target.
2. **Set RAG status** per workstream using fixed rules:
   - Green: on track for the next milestone date.
   - Amber: at risk; a slip is likely without action, or a metric is over 10 percent off target.
   - Red: milestone will be missed, or a blocker has no owner.
3. **Write risks and asks.** Every amber or red item needs an owner and a specific ask (decision, budget, person, deadline).
4. **Cut activity lists** to the 3 to 5 things that moved a metric or milestone.

## Format

```markdown
# <Team/Project> weekly update, week of <date>

**Overall: <Green/Amber/Red>.** <One sentence: the most important thing this week.>

## Decisions needed
1. <Decision>, by <date>, from <who>. Options: A / B. Recommendation: A, because ...

## Metrics
| Metric | This week | Last week | Target | Trend |
|---|---|---|---|---|

## Workstreams
| Workstream | Status | Next milestone | Note |
|---|---|---|---|

## Risks
| Risk | Impact | Owner | Mitigation |
|---|---|---|---|

## Done this week
- ...

## Next week
- ...
```

## Rules

- One page. If it does not fit, cut detail, not decisions.
- No status without a reason. "Amber" alone is not useful.
- Numbers come from the inputs only. Do not estimate missing metrics; mark them "no data".
