# CallLog Celery safety release — manual deployment only

## Findings and scope
The package initializer was empty and shared-task publishers had no explicit routes.
This is a confirmed startup defect and a plausible explanation for publication to
`celery`, NOT proof of the live producer. Verify the running web process, release,
settings and task binding before attributing the backlog. Shell settings alone do
not establish the configuration of an already-running producer.

The patch does not move, inspect, delete or replay existing Redis messages. It does
not change broker/result/cache/Channels DB URLs or any HR Payroll configuration.
The intended queue defaults to `calllog_system`; a different application-owned
queue can be configured. `celery`, empty names, comma-separated names and unsafe
characters are rejected. Project task routes use the same queue. No service uses
`-B`, and no Beat service is supplied.

## Policy and compatibility
- `MISSED_CALL_MAX_AGE_SECONDS=5400`: calls must be less than 90 minutes old.
  This leaves a 30-minute recovery window after the last 60-minute reminder.
  The configured value must exceed 3600. All comparisons use aware call timestamps.
- `CALL_ROUTING_MAX_AGE_SECONDS=5400`: routing tasks and WhatsApp preparation/sending
  reject historical, future or invalid-time calls. The synchronous routing decision
  engine remains available for historical audit/backfill, but cannot prepare stale sends.
- Devices must be registered, active, unblocked, not deleted and still assigned to
  the call's branch. Missing records, resolved missed calls and superseded steps skip.
- Scheduling publishes the highest currently due step and remaining future steps at
  original-call deadlines; it does not send every missed intermediate step at once.
- `MISSED_CALL_SWEEP_BATCH_SIZE=200` bounds total examined candidates per sweep.
  Per-step database reservations coordinate schedulers and overlapping sweeps.
- `MISSED_CALL_QUEUE_LEASE_SECONDS=300`: queued reservations may be republished five
  minutes after their ETA. Lost publication can recover through the sweep; duplicate
  broker messages share the same send claim. No automatic queue recovery occurs while
  Beat is stopped. Recovery may skip intermediate steps if their window has passed.
- `SEND_CLAIM_TIMEOUT_SECONDS=300`: abandoned sends require reconciliation. A later
  sender invocation marks an overdue sending claim ambiguous; untouched abandoned
  claims remain visibly sending and must be included in operator checks. A timeout
  is NOT permission to resend. No automatic reset of sending/ambiguous claims exists.
- Failed FCM sends do not advance notification_step. A failed step is not automatically
  retried because the existing notification service returns only a boolean, which
  cannot prove non-delivery. An exception blocks subsequent steps as ambiguous.
- WhatsApp accepts only queued state, rechecks flags, age and normalized recipient,
  and atomically claims the message before network I/O. Timeout/network/5xx/malformed
  success/missing provider ID becomes ambiguous, with no automatic resend. Known
  permanent errors become failed. Duplicate routing preparation never revives a row.
- Provider idempotency support has NOT been established. No exactly-once guarantee:
  crashes after provider acceptance but before recording success require reconciliation.
- Settings are process-local. Changing .env does not alter running worker flags;
  restart the dedicated worker to apply changes. A network request already started
  cannot be recalled. Business/device state can also change during network I/O.
- Result storage is disabled by default, with one-hour retention if explicitly used.
  This is not broker message expiry. ETA tasks are capped at 100 per worker (Celery 5.6).
- Queue concurrency=1 and prefetch=1 are conservative starting values, not an assertion
  that the VPS has sufficient spare memory.

Migrations: calllogs 0008 creates per-step reminder claims; callrouting 0003 adds the
ambiguous status choice. No legacy message transformation or historical data replay.
Stop old CallLog workers before migration/activation: mixed worker versions bypass
claims. Leave additive schema in place during rollback. Old send code is unsafe for
ambiguous records and MUST NOT be restarted against these tasks.

## Safe local validation
Never run ordinary manage.py against the root .env for these tests.
PowerShell, from the repository root:

```powershell
$env:DJANGO_SETTINGS_MODULE='config.settings.test_tasks'
$env:CELERY_BROKER_URL='memory://'
$env:CELERY_RESULT_BACKEND='cache+memory://'
venv\Scripts\python.exe -m config.offline_test_runner test apps.calllogs.test_task_safety
venv\Scripts\python.exe -m config.offline_test_runner makemigrations calllogs callrouting --check --dry-run
```

The runner blocks outbound socket connections before Django startup. Test settings
never inherit base settings or read .env. SQLite and the broker are in-memory;
external notifications/providers are mocked. The default schema migrations run only
on the disposable test DB. PostgreSQL concurrent row-lock tests are skipped on SQLite.
Before deployment, run these tests against a disposable local PostgreSQL instance
with separate explicit test settings and a localhost-only network allowlist; do not
substitute production credentials. Also exercise Redis transport/ETA limits with an
isolated local Redis instance and a dedicated temporary database/queue. Neither
PostgreSQL concurrency nor Redis transport behavior is certified by the offline run.

## Environment and preflight
Required existing environment: DJANGO_SECRET_KEY (use the actual setting's key),
POSTGRES_DB/USER/PASSWORD/HOST/PORT, ALLOWED_HOSTS, and existing provider credentials
only where outbound sends are approved. Confirm the secret variable name in base.py
before provisioning; never print environment dumps. Celery-specific variables:

```
DJANGO_SETTINGS_MODULE=config.settings.prod
CELERY_TASK_DEFAULT_QUEUE=calllog_system
CELERY_BROKER_URL=<reviewed application broker URL>
CELERY_RESULT_BACKEND=<reviewed application result backend URL>
ENABLE_CALL_ROUTING=False
CALL_ROUTING_DRY_RUN=True
ENABLE_CALL_ROUTING_WHATSAPP=False
MISSED_CALL_MAX_AGE_SECONDS=5400
CALL_ROUTING_MAX_AGE_SECONDS=5400
MISSED_CALL_SWEEP_BATCH_SIZE=200
MISSED_CALL_QUEUE_LEASE_SECONDS=300
SEND_CLAIM_TIMEOUT_SECONDS=300
```

Use identical queue/broker/settings for web producers and worker. Put production
values in `/etc/calllog/worker.env` (root-owned, mode 0600), without shell exports;
systemd reads it before dropping privileges. This file is deliberately NOT supplied
with real values. The service environment overrides root .env values. Avoid stale
CELERY_CONFIG_MODULE or custom loaders; inspect effective settings without exposing
URLs or credentials. Do not change shared Redis databases, key prefixes, eviction,
visibility timeout or persistence without coordinating all applications.

## Exact later deployment sequence (operator execution, not run by this patch)
1. Review/test/commit this focused patch through your normal Git process. Record the
   approved release SHA and previous SHA. Preserve unrelated local changes. On the
   server require a clean deployment checkout; do not discard local modifications.
2. Verify available memory, broker ownership, queue contents and dependencies first.
   Confirm Celery 5.6.2 and all installed application dependencies. No dependency
   installation is performed automatically. Stop only a dedicated CallLog worker if
   one exists; do not stop HR Payroll. Keep CallLog Beat stopped. Pause CallLog web
   ingestion during migration/release switching using the existing web service's
   actual name (not known from this repository).
3. In `/var/www/spacallapp`, deploy the reviewed Git release:

```sh
git fetch origin
git status --short
git switch --detach <APPROVED_RELEASE_SHA>
```

4. Run with the reviewed environment loaded by systemd, without printing it:

```sh
sudo systemd-run --wait --pipe --collect --uid=www-data --gid=www-data --property=WorkingDirectory=/var/www/spacallapp --property=EnvironmentFile=/etc/calllog/worker.env /var/www/spacallapp/venv/bin/python manage.py migrate --plan --settings=config.settings.prod
```

   Review the entire pending migration plan. If it includes unrelated historical
   migrations, resolve that separately. With backups and the plan approved:

```sh
sudo systemd-run --wait --pipe --collect --uid=www-data --gid=www-data --property=WorkingDirectory=/var/www/spacallapp --property=EnvironmentFile=/etc/calllog/worker.env /var/www/spacallapp/venv/bin/python manage.py migrate --noinput --settings=config.settings.prod
sudo systemd-run --wait --pipe --collect --uid=www-data --gid=www-data --property=WorkingDirectory=/var/www/spacallapp --property=EnvironmentFile=/etc/calllog/worker.env /var/www/spacallapp/venv/bin/python -m config.verify_task_config
```

5. The preflight loads Django and checks binding/routes; it does not publish tasks.
   Verify `calllog_system` is exclusively owned and inspect its existing work before
   starting. Reminder sends are live when this worker runs; routing dry-run does not
   disable FCM. Do not start until fresh reminder sends are approved and test gates pass.
6. Install the reviewed unit, then start only that worker:

```sh
sudo install -m 0644 infrastructure/systemd/calllog-worker.service /etc/systemd/system/calllog-worker.service
sudo systemctl daemon-reload
sudo systemctl start calllog-worker.service
sudo systemctl status calllog-worker.service --no-pager
sudo journalctl -u calllog-worker.service -n 100 --no-pager
```

   Inspect logs privately for the expected queue only, concurrency 1 and successful
   task imports. Confirm producer binding under the actual web entry point; restart
   only the existing CallLog web service through its documented release procedure.
   Enable the worker on boot only after acceptance:

```sh
sudo systemctl enable calllog-worker.service
```

7. Keep Beat stopped until disposable PostgreSQL concurrency and Redis transport
   tests, repeated-sweep tests, resource monitoring and periodic overlap review pass.
   Enable outbound WhatsApp only after explicit operational approval and a canary.
   No Beat installation/start command is intentionally provided.

## Monitoring and rollback
Monitor the intended queue's depth/oldest age and arrival/completion rate, failed and
ambiguous claims, sending claims older than five minutes, send success/failure rate,
worker memory, Redis latency/memory/swap, database load and rejected stale tasks.
Monitor legacy queue growth separately using bounded metadata reads; never use a
full list dump, destructive pop, FLUSHDB or a worker subscription as inspection.
Record baseline and after-release values without message bodies or credentials.

On regression: stop `calllog-worker.service`, keep Beat stopped, pause affected
producers, disable routing sends in reviewed environment and restart affected web
processes. Revert to the recorded Git SHA using the normal release procedure. Keep
new tables/status data; do not reverse/drop claim migrations automatically. Do not
restart the old worker/send path. A rollback does not undo delivered notifications.
Reconcile in-flight sends before any recovery/restart.

## Separate legacy backlog decision
Do not subscribe the new worker to `celery`, purge it, or migrate it automatically.
Before a separately approved recovery, establish each message's application owner,
producer/release, task type/version, original call timestamp, ETA/expiry/retry count,
database existence, resolved state, device/recipient eligibility, existing delivery
claims and provider delivery evidence. Three samples cannot characterize 1.29M items.
Unknown task names/ownership remain quarantined. Old scheduler tasks should not be
replayed merely to recreate reminders. Prefer reconstructing eligible business work
from database state after approval. Classify each group for retain/quarantine,
selective reconstruction, or discard; document counts and rollback/evidence needs.
For ambiguous sends, correlate provider logs/callbacks manually. Mark delivered only
with evidence; allow an explicitly reviewed new attempt only with verified non-send,
current eligibility and recorded operator authorization. No reset script is provided.

## Urgent separate follow-ups
Admin update escalation; plaintext password storage/exposure; access-token/session
revocation and WebSocket authorization; cross-branch writes; export metadata/file
ownership; OTP throttling; webhook sends inside transactions; retention/performance.
These are deliberately outside this focused patch.
