# DoubleTick Setup Checklist

Use this checklist before enabling automatic DoubleTick lead distribution in production.

## Commands

Preview channel changes without writing:

```bash
python manage.py setup_doubletick_channels --dry-run
```

Create or update default WABA channels:

```bash
python manage.py setup_doubletick_channels
```

Create only missing channels and leave existing channel rows unchanged:

```bash
python manage.py setup_doubletick_channels --only-missing
```

Audit channel, webhook, bot, mapping, visibility, and integration health:

```bash
python manage.py audit_doubletick_setup
```

## Default WABA Channels

| Name | WABA | State | City | Branch Group |
| --- | --- | --- | --- | --- |
| Spa Advisor Main | 917506359139 |  |  | Main |
| Spa Advisor Main 800 | 918976822800 | All India |  | Main |
| Spa Advisor Rajasthan | 918976822801 | Rajasthan |  | Rajasthan |
| Spa Advisor Gujarat | 918976822802 | Gujarat |  | Gujarat |
| Spa Advisor Bangalore | 918976822803 | Karnataka | Bangalore | Bangalore |

All WABA numbers are stored as digits only.

## DoubleTick Dashboard

Configure the CRM webhook URL in DoubleTick and enable all lead-relevant events available in the dashboard:

- Incoming message / message received
- Interactive reply / button reply / list reply
- Template reply / flow response
- Message sent
- Message delivered
- Message read
- Message failed
- Agent message / assigned user event, if available
- Customer custom field updated, if available
- Template status event, if available

## Required CRM Data

- Active `DoubleTickChannel` records exist for every selected WABA/API channel.
- Channel-specific bot triggers are configured for Rajasthan, Gujarat, and Bangalore when those flows should differ.
- A default active bot trigger exists as fallback.
- `DoubleTickLeadArea` records exist for all service areas.
- `DoubleTickAreaAlias` records include common spelling, city, area, and ad text variants.
- `DoubleTickLeadAreaBranch` mappings connect lead areas to active branches.
- Branch groups exist for Main, Rajasthan, Gujarat, and Bangalore.
- Team member mappings exist for DoubleTick agents that should appear by name.

## Quick Shell Checks

```bash
python manage.py shell -c "from apps.doubletick.models import DoubleTickChannel; print(DoubleTickChannel.objects.values_list('name','waba_number','is_active'))"
python manage.py shell -c "from apps.bots.models import BotTrigger; print(BotTrigger.objects.filter(is_active=True, bot__is_active=True).count())"
python manage.py shell -c "from apps.doubletick.models import DoubleTickWebhookLog; print(DoubleTickWebhookLog.objects.filter(processed=False).count())"
python manage.py shell -c "from apps.doubletick.models import DoubleTickLead; print(DoubleTickLead.objects.filter(visibilities__isnull=True).distinct().count())"
```

## Expected Routing

1. Channel-specific active trigger wins first.
2. Keyword/source/city/lead-type triggers are used next.
3. Default active trigger is used as fallback.
4. If no trigger exists, the default booking bot is created and used.

Webhook processing never creates a new WABA channel automatically. Unknown channel payloads are saved, marked with `channel_not_found`, and reported by `audit_doubletick_setup`.
