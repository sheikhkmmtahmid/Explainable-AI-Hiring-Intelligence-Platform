# Monitoring and alerting plan

This describes what should actually be watched once this app is running somewhere real, not a list of tools for their own sake. Nothing here is wired up to a paid monitoring service yet. This is the plan for doing that, written down so it does not depend on being remembered.

## What exists right now

A health check endpoint at `/healthz/` checks that the database and cache are actually reachable, not just that the process is running. It returns a 200 with `{"status": "healthy"}` when both are fine, and a 503 with which check failed when they are not. Any uptime monitor (even a free one) can poll this on a short interval and page someone the moment either dependency goes down.

Structured JSON logging is on for the production settings module (`config/settings/huggingface.py`), through `config/logging_formatters.py`. Every log line is one JSON object with a timestamp, level, logger name, and message, plus whatever extra fields a given log call attaches. This is what makes the rest of this plan possible. Free text logs cannot be reliably alerted on, structured ones can.

`SENTRY_DSN` already exists as a settings value read from the environment (see `.env.example`), so error tracking is a matter of setting that variable and installing the Sentry SDK, not a new integration to build.

## What should be watched, and why

**Uptime and dependency health.** Poll `/healthz/` every one to five minutes. Alert immediately if it returns anything other than 200, and alert if it does not respond at all within a reasonable timeout. This is the single highest value check, since it catches the two most common real failure modes for this app: TiDB Cloud connectivity dropping, or Redis becoming unreachable.

**Error rate.** Once Sentry (or an equivalent) is wired in, alert on a spike in unhandled exceptions, not just their existence. A handful of 404s is normal. A sudden jump in 500s is not.

**Match scoring pipeline health.** This app found a real, silent bug this session where match scores were being computed incorrectly for weeks without anything noticing. The dedicated tests in `tests/test_scoring_pipeline.py` catch regressions before deployment, but that does not help if something drifts in production data itself (for example, a `learned_weights.json` file reappearing with bad values). Worth adding: a scheduled job that spot checks a sample of real match scores against the test assertions already written (weights sum to 1, semantic score is never near zero on average) and alerts if either ever fails outside of tests.

**Celery task failures.** Job matching, embedding generation, and skill extraction all run through Celery. A task that silently fails leaves a candidate or job without an embedding, which then quietly excludes them from matching with no visible error to a user. Worth logging and alerting on task failure counts, not just relying on `CELERY_TASK_ALWAYS_EAGER` style local testing.

**Payment webhook failures.** Stripe and SSLCommerz both confirm payment through webhooks, not the initial request. A webhook that fails to process (bad signature, timeout, unhandled exception) can leave a subscription in an inconsistent state that nobody notices until a customer complains. Worth alerting on any webhook handler exception, specifically, not lumped in with general error rate.

## What this plan deliberately does not include yet

Real infrastructure metrics (CPU, memory, database query latency at the TiDB level) are not covered here because they depend on where this is actually deployed, and guessing at a specific cloud provider's dashboard setup before that decision is made would be premature. The moment a real deployment target is chosen, that provider's own metrics (AWS CloudWatch, TiDB Cloud's own dashboard, or similar) should be added to this list, not reinvented.
