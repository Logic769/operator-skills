# Contributing

Thanks for helping. Most contributions take under an hour, and you do not need to be a developer to add a good skill.

## Ways to help

- **Add a new skill** for a job you do every week. Check the roadmap in the README and open issues first.
- **Improve a skill** that gave you a bad result. Include the input that failed (with real data removed).
- **Add an example** input file to a skill's `examples/` folder.
- **Fix docs**, typos and unclear steps.

## Add a skill in 5 steps

1. Fork the repo and create a branch: `git checkout -b skill/<skill-name>`.
2. Copy the template: `mkdir skills/<skill-name> && cp templates/SKILL_TEMPLATE.md skills/<skill-name>/SKILL.md`.
3. Fill it in. Keep it under about 300 lines. Put long reference material in a separate file inside the folder and link to it.
4. Run the linter: `python scripts/validate_skills.py`.
5. Open a pull request using the template. Tell us what you tested it on.

## Rules a skill must pass

- Folder name is lowercase kebab-case and matches `name` in the frontmatter.
- `description` is one sentence, under 1024 characters, and says when to use the skill.
- No secrets, API keys, personal data or real client names.
- Scripts use only the Python standard library and run with Python 3.9+.
- Scripts print clear errors and exit non-zero on failure.
- Write in plain English. No em dashes (the linter checks).

## Review

A maintainer aims to respond within 3 days. We may suggest changes to keep skills consistent with the design rules in the README. Once merged you are listed in the contributors graph and in the skill's `Credits` line if you want.

## Code of conduct

Be kind and specific. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
