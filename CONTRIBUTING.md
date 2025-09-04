# Contributing to MetaArt

Thank you for your interest in contributing! This guide helps you get started.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Branching & Workflow](#branching--workflow)
- [Commit Messages](#commit-messages)
- [Pull Request Checklist](#pull-request-checklist)
- [Issue Guidelines](#issue-guidelines)
- [Style & Tooling](#style--tooling)
- [Testing](#testing)
- [Documentation](#documentation)
- [Security](#security)
- [License Notes](#license-notes)
- [Contact](#contact)

## Code of Conduct
All participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to REPLACE_WITH_CONTACT.

## Ways to Contribute
- Bug reports / issue triage
- Feature proposals
- Improving documentation, examples, or tutorials
- Adding generators / modules / assets (respecting asset licensing)
- Tooling (CI, scripts, tests)

## Development Setup
```bash
git clone https://github.com/AndroDoge/MetaArt.git
cd MetaArt
# Install dependencies (add actual commands, e.g. pip install -r requirements.txt or npm install)
```
Optional: create and activate virtual environment or Node version via nvm.

## Branching & Workflow
1. Create an issue (optional but recommended for larger changes).
2. Branch from main: `feature/<short-name>` or `fix/<short-name>`
3. Keep changes focused and small.
4. Rebase onto latest main before opening PR (avoid large merge commits).
5. Open PR with clear description, screenshots/GIFs if visual.

## Commit Messages
Prefer Conventional Commits format:
- feat: add new generator for layered gradients
- fix: correct color blending edge case
- docs: update README roadmap
- chore: dependency bump
- test: add snapshot test for noise pattern

## Pull Request Checklist
- [ ] Code compiles / runs
- [ ] Lint passes
- [ ] Tests added / updated (if applicable)
- [ ] Docs / README updated (if behavior/user-visible changes)
- [ ] No secrets or sensitive data
- [ ] SPDX headers present (script: `python scripts/add_spdx_headers.py`)

## Issue Guidelines
When opening an issue include:
- Summary
- Steps to reproduce (if bug)
- Expected vs actual
- Environment (OS, Python/Node version, etc.)
- Screenshots if visual

Labels to use:
- `bug`, `enhancement`, `documentation`, `question`, `good first issue`, `help wanted`.

## Style & Tooling
- SPDX: `AGPL-3.0-only` in headers
- Formatting: (specify once tooling chosen, e.g. black / prettier)
- Keep functions cohesive; avoid overly large files
- Add docstrings / JSDoc for public APIs

## Testing
Add tests under `tests/` mirroring source structure.
```bash
pytest            # example (Python)
npm test          # or equivalent
```
Provide at least one minimal usage example for new modules.

## Documentation
- Update README or create a file under `docs/` for larger topics (e.g. `docs/generators.md`).
- Include diagrams or small PNG/GIF examples when meaningful.

## Security
If you find a vulnerability or exploit vector, DO NOT open a public issue. Email REPLACE_WITH_CONTACT (or use GitHub Security Advisory) with details and reproduction.

## License Notes
Source code: AGPL-3.0-only (see LICENSE).
Commercial / alternative license inquiries: see NON-COMMERCIAL-ADDENDUM.md and contact author.

## Contact
Questions? Reach out via issue or REPLACE_WITH_CONTACT.

---
Thank you for helping improve MetaArt!

---