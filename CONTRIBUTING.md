# Contributing

Thanks for helping. Most contributions take under an hour, and you do not need to be a developer to add a good skill.

## Ways to help

- **Add a new skill** for a job you do every week. Check the roadmap in the README and open issues first.
- **Improve a skill** that gave you a bad result. Include the input that failed, with any real data removed.
- **Add an example** input file to a skill's `examples/` folder.
- **Fix docs**, typos and unclear steps.

## Add a skill in 5 steps

1. Fork the repo and create a branch: `git checkout -b skill/<skill-name>`.
2. Copy the template: `mkdir skills/<skill-name> && cp templates/SKILL_TEMPLATE.md skills/<skill-name>/SKILL.md`.
3. Fill it in. Keep it under about 300 lines. Put long reference material in a separate file inside the folder and link to it.
4. Run the checks: `python3 scripts/validate_skills.py` and, if you touched a script, `python3 -m unittest discover -s tests`.
5. Open a pull request using the template. Tell us what you tested it on.

## Rules a skill must pass

- Folder name is lowercase with hyphens, at most 64 characters, matches `name` in the frontmatter, and does not contain "claude" or "anthropic".
- `description` says what the skill does, then "Use when ..." with the words people actually type. Under 1024 characters, no `<` or `>`. If it contains `: ` wrap it in quotes.
- Scripts are called as `python3 ${CLAUDE_SKILL_DIR}/scripts/<file>.py` so they work from any folder.
- No secrets, API keys, personal data, or real people or companies. Use `.example` domains such as `acme.example`.
- Scripts use only the Python standard library, run on Python 3.9+, read only the files they are given, make no network calls, print clear errors, and exit non-zero on failure. Add tests in `tests/`.
- Write in plain English. No em dashes (the linter checks).

## Review

A maintainer reviews pull requests as soon as possible, usually within a few days. We may suggest changes to keep skills consistent with the design rules in the README. If you want credit inside the skill, add yourself to its `Credits` line.

## Code of conduct

Be kind and specific. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
