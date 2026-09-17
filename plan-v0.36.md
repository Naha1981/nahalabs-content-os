# v0.36 Plan
1. Add deterministic cron matching and next-run calculation.
2. Add autonomous worker with once/continuous modes.
3. Persist next-run timestamps after each execution.
4. Prevent duplicate execution in a scheduler minute.
5. Add regression tests.
6. Later: host the worker on Trigger.dev or another always-on runtime; local worker is the development fallback.
