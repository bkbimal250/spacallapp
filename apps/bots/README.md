# CRM Bot Builder

`apps.bots` provides configurable WhatsApp bot workflows for DoubleTick conversations.

## Main Pieces

- `Bot` and `BotFlow`: multiple bots and publishable workflow versions.
- `BotNode`, `BotNodeOption`, `BotTransition`: node-based flow builder.
- `BotSession`: per customer/conversation state, including city, area, branch, intent, language, retries, and fallback state.
- `BotExecutionLog`: idempotency and audit log for each bot action.
- `BotIntegration`, `BotApiCallLog`, `BotSheetSyncLog`: external API and Google Sheets-ready integration structure.

## DoubleTick Flow

1. DoubleTick webhook saves customer, conversation, message, and lead.
2. `BotEngine.handle_incoming_message(conversation, lead, message)` runs.
3. The engine finds an active bot by channel/campaign/default trigger.
4. The session continues from its current node.
5. Outbound messages are sent with `DoubleTickOutboundService` and saved in `DoubleTickMessage`.

Duplicate provider retries are guarded by `BotExecutionLog.idempotency_key`.

## Dynamic Location Sources

The bot does not hardcode locations. Dynamic city, area, and branch choices are loaded from:

- `branches.Branch`
- `doubletick.DoubleTickLeadArea`
- `doubletick.DoubleTickAreaAlias`
- `doubletick.DoubleTickLeadAreaBranch`

If too many options exist, the engine paginates WhatsApp list rows and includes `More locations` plus `Type your area`.

## Manual Commands

Run these only after migrations are applied:

```bash
python manage.py rebuild_bot_sessions_from_doubletick
python manage.py test_bot_flow --lead-id <uuid> --text "Hello"
python manage.py fix_raw_area_generic_messages
python manage.py backfill_doubletick_unmatched_leads
python manage.py backfill_doubletick_visibility
python manage.py reprocess_doubletick_logs --only-unlinked
```

## API

Bot builder APIs are under `/api/v1/bots/`.

Common endpoints:

- `/api/v1/bots/bots/`
- `/api/v1/bots/flows/`
- `/api/v1/bots/nodes/`
- `/api/v1/bots/node-options/`
- `/api/v1/bots/transitions/`
- `/api/v1/bots/triggers/`
- `/api/v1/bots/sessions/`
- `/api/v1/bots/execution-logs/`
- `/api/v1/bots/test-flow/`

DoubleTick manual actions:

- `POST /api/v1/doubletick/leads/{lead_id}/reply/`
- `POST /api/v1/doubletick/mobile/leads/{lead_id}/reply/`
- `POST /api/v1/doubletick/leads/{lead_id}/send-location-options/`
- `POST /api/v1/doubletick/mobile/leads/{lead_id}/send-location-options/`
- `POST /api/v1/doubletick/leads/{lead_id}/handover/`
- `POST /api/v1/doubletick/mobile/leads/{lead_id}/handover/`
- `POST /api/v1/doubletick/leads/{lead_id}/run-bot-node/`
- `POST /api/v1/doubletick/mobile/leads/{lead_id}/run-bot-node/`
