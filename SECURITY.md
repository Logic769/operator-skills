# Security policy

## Scope

This repo contains Agent Skills (Markdown instructions) and small Python scripts that run on your own machine. The scripts:

- use only the Python standard library,
- read only the file you pass in,
- write only the output files you name, or files next to the input,
- make no network calls and never execute content from the files they read.

Relevant problems include a script that can be made to write outside the paths it was given, crash in a way that loses data, execute input, or produce output that is unsafe to open (for example, spreadsheet formulas). Skill instructions that could lead an agent to leak data or take unsafe actions are also in scope.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private reporting instead: go to the **Security** tab of this repository and click **Report a vulnerability**.

You will get an acknowledgement within 7 days. Fixes are released as soon as they are ready, and reporters are credited unless they prefer not to be.

## Supported versions

Only the latest version on the `main` branch is supported.
