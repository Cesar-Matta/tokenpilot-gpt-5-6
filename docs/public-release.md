# Public release checklist

Run this checklist before making the repository public.

```bash
python scripts/public_release_check.py
python scripts/validate_skill.py
pytest
ruff check .
git status --short
git log --all --oneline
```

Verify manually:

- No API key, token, private key, cookie, credential file, or `.env` file is tracked.
- No local machine path, internal hostname, customer data, personal data, or private product reference appears in files or Git history.
- Examples use `YOUR_TOKENPILOT_HOST`, placeholder keys, and fictional data only.
- README badges and project links contain the real public GitHub owner.
- The model catalog has a visible pricing date and source link.
- The independent-project disclaimer is present.

The repository checker is a fast guardrail, not a substitute for secret scanning or human review.
