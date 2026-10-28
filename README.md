# operator-skills

Open-source Agent Skills for the people who run the business: operations, GTM, RevOps, customer success and automation builders.

Each skill is a folder with a `SKILL.md` that teaches Claude (or any agent that reads the Agent Skills format) how to do one recurring job well, the same way every time. Some skills ship small, dependency-free scripts so the agent runs real code instead of guessing.

> Status: early. Skills are battle-tested in real client work, but the collection is small. Contributions are very welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Skills

| Skill | What it does | Has script |
|---|---|---|
| [lead-list-cleanup](skills/lead-list-cleanup) | Normalizes, validates and dedupes prospect CSVs before they hit a CRM or sequencer | Yes |
| [icp-lead-scoring](skills/icp-lead-scoring) | Scores leads against a written ICP rubric with a reason for every score | No |
| [cold-outreach-sequence](skills/cold-outreach-sequence) | Writes a short, specific 3-step outbound sequence from a lead and an offer | No |
| [n8n-workflow-review](skills/n8n-workflow-review) | Audits an exported n8n workflow JSON for reliability and security issues | Yes |
| [sop-writer](skills/sop-writer) | Turns a messy process description into a standard operating procedure | No |
| [call-notes-to-crm](skills/call-notes-to-crm) | Converts raw call notes or transcripts into CRM fields, next steps and a follow-up email | No |
| [weekly-ops-report](skills/weekly-ops-report) | Builds a one-page weekly status report with RAG status, risks and asks | No |

## Install

### Claude Code

```bash
git clone https://github.com/zeebyx/operator-skills.git
# Personal skills (all projects)
cp -r operator-skills/skills/* ~/.claude/skills/
# Or project skills (one repo)
cp -r operator-skills/skills/* .claude/skills/
```

### Claude apps (claude.ai, desktop)

Zip a single skill folder (for example `skills/sop-writer`) and upload it under Settings > Capabilities > Skills.

### Claude API / Agent SDK

Point your agent's skills directory at `skills/`, or upload a skill folder through the Skills API.

## Design rules

Every skill in this repo follows the same rules, so they behave predictably:

1. **One job per skill.** If the description needs "and", it is probably two skills.
2. **The description decides when it runs.** It states the trigger in plain words a user would actually type.
3. **Deterministic work goes in scripts.** Dedupe, parse, validate and count in code. Use the model for judgment and writing.
4. **Scripts use only the Python standard library.** No install step, runs anywhere Python 3.9+ runs.
5. **Output formats are spelled out.** The skill shows the exact shape of what it returns.
6. **No secrets, no client data.** Examples use invented companies.

`python scripts/validate_skills.py` checks rules that can be checked automatically. CI runs it on every pull request.

## Repo layout

```
skills/<skill-name>/SKILL.md        required, with name + description frontmatter
skills/<skill-name>/scripts/        optional helper scripts (stdlib only)
skills/<skill-name>/examples/       optional sample inputs
templates/SKILL_TEMPLATE.md         start here for a new skill
scripts/validate_skills.py          repo linter
```

## Roadmap

Skills we want next (good first contributions, see open issues):

- `churn-risk-review` for customer success account reviews
- `pipeline-hygiene` for stale deals and missing fields
- `invoice-chaser` for polite, escalating payment reminders
- `hubspot-property-audit` and `salesforce-field-audit`
- `zapier-to-n8n-migration` planning
- `job-post-to-icp` for hiring-signal prospecting
- `qbr-deck-outline` for quarterly business reviews

## License

MIT. Use these in commercial work. Attribution appreciated, not required.

Maintained by [Nitin Sarkar](https://github.com/zeebyx) at [After Machines](https://aftermachines.com).
