# ErrLab: project context
Goal: Flagsmith Toggle Wars Track 01 entry. One well-designed A/B test, not a big app.
Hypothesis: concrete fix in a CLI error message raises first-retry recovery by >=10pp vs terse.
Stack: Python 3.10+, flagsmith SDK >=6.3.0 (remote evaluation, enable_events=True).
Flag: error_message_style, variants terse (control) / with_fix / with_fix_and_link.
Primary metric: retry_succeeded. Exposure recorded when the error message is displayed.
Rules:
- Read the Flagsmith docs (docs.flagsmith.com/experimentation/run-an-experiment) before writing SDK code. Never guess signatures.
- If something fails, stop and show me the exact error. Don't work around it.
- Never commit or print API keys. Use .env (gitignored).
- Work in small steps; verify each; keep code readable. I must be able to explain every line.
- Every user (including simulated bots) needs a stable identifier.
