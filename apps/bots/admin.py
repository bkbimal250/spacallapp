from django.contrib import admin

from .models import (
    Bot,
    BotApiCallLog,
    BotDataSource,
    BotExecutionLog,
    BotFallbackRule,
    BotFlow,
    BotHandoverRule,
    BotIntegration,
    BotMessageTemplate,
    BotNode,
    BotNodeOption,
    BotSession,
    BotSessionVariable,
    BotSheetSyncLog,
    BotTransition,
    BotTrigger,
)


class BotNodeOptionInline(admin.TabularInline):
    model = BotNodeOption
    fk_name = "node"
    extra = 0
    fields = ("label", "value", "payload_id", "next_node", "action", "order", "is_active")


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "bot_type", "is_active", "priority", "updated_at")
    list_filter = ("bot_type", "is_active")
    search_fields = ("name", "slug", "description")
    actions = ["activate", "deactivate", "clone_bot"]

    def activate(self, request, queryset):
        queryset.update(is_active=True)

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)

    def clone_bot(self, request, queryset):
        for bot in queryset:
            clone = Bot.objects.create(
                name=f"{bot.name} Copy",
                slug=f"{bot.slug}-copy",
                bot_type=bot.bot_type,
                description=bot.description,
                default_language=bot.default_language,
                is_active=False,
                priority=bot.priority,
                config=bot.config,
            )
            for flow in bot.flows.all():
                BotFlow.objects.create(bot=clone, name=flow.name, version=flow.version, is_active=False, is_published=False, config=flow.config)


@admin.register(BotFlow)
class BotFlowAdmin(admin.ModelAdmin):
    list_display = ("name", "bot", "version", "is_active", "is_published", "published_at")
    list_filter = ("is_active", "is_published", "bot")
    search_fields = ("name", "bot__name")
    actions = ["publish"]

    def publish(self, request, queryset):
        for flow in queryset:
            flow.bot.flows.update(is_active=False)
            flow.is_active = True
            flow.is_published = True
            from django.utils import timezone

            flow.published_at = timezone.now()
            flow.save()


@admin.register(BotNode)
class BotNodeAdmin(admin.ModelAdmin):
    list_display = ("name", "flow", "node_type", "language", "order", "is_active")
    list_filter = ("node_type", "is_active", "flow__bot")
    search_fields = ("name", "message_text", "flow__bot__name")
    inlines = [BotNodeOptionInline]


@admin.register(BotNodeOption)
class BotNodeOptionAdmin(admin.ModelAdmin):
    list_display = ("label", "node", "value", "payload_id", "next_node", "order", "is_active")
    list_filter = ("is_active", "action")
    search_fields = ("label", "value", "payload_id")


@admin.register(BotTransition)
class BotTransitionAdmin(admin.ModelAdmin):
    list_display = ("flow", "from_node", "to_node", "priority", "is_active")
    list_filter = ("is_active", "flow")


@admin.register(BotTrigger)
class BotTriggerAdmin(admin.ModelAdmin):
    list_display = ("bot", "trigger_type", "channel", "city", "branch", "is_default", "is_active", "priority")
    list_filter = ("trigger_type", "is_default", "is_active", "channel")
    search_fields = ("bot__name", "source_campaign", "city", "lead_type")


@admin.register(BotSession)
class BotSessionAdmin(admin.ModelAdmin):
    list_display = ("bot", "conversation", "lead", "current_node", "intent", "status", "fallback_count", "last_activity_at")
    list_filter = ("status", "intent", "bot")
    search_fields = ("conversation__customer__phone_number", "lead__phone_number", "selected_city", "selected_area")


@admin.register(BotSessionVariable)
class BotSessionVariableAdmin(admin.ModelAdmin):
    list_display = ("session", "key", "updated_at")
    search_fields = ("key",)


@admin.register(BotExecutionLog)
class BotExecutionLogAdmin(admin.ModelAdmin):
    list_display = ("session", "node", "status", "event", "created_at")
    list_filter = ("status", "event")
    search_fields = ("idempotency_key", "error_message")


@admin.register(BotMessageTemplate)
class BotMessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "bot", "language", "template_type", "is_active")
    list_filter = ("language", "template_type", "is_active")
    search_fields = ("name", "text")


@admin.register(BotDataSource)
class BotDataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "is_active")
    list_filter = ("source_type", "is_active")


@admin.register(BotIntegration)
class BotIntegrationAdmin(admin.ModelAdmin):
    list_display = ("name", "integration_type", "is_active", "updated_at")
    list_filter = ("integration_type", "is_active")


@admin.register(BotApiCallLog)
class BotApiCallLogAdmin(admin.ModelAdmin):
    list_display = ("integration", "node", "status_code", "success", "created_at")
    list_filter = ("success", "status_code")


@admin.register(BotSheetSyncLog)
class BotSheetSyncLogAdmin(admin.ModelAdmin):
    list_display = ("integration", "lead", "success", "created_at")
    list_filter = ("success",)


@admin.register(BotHandoverRule)
class BotHandoverRuleAdmin(admin.ModelAdmin):
    list_display = ("bot", "name", "assign_user", "assign_branch", "is_active", "priority")
    list_filter = ("is_active", "bot")


@admin.register(BotFallbackRule)
class BotFallbackRuleAdmin(admin.ModelAdmin):
    list_display = ("bot", "name", "retry_number", "next_node", "handover_after", "is_active")
    list_filter = ("is_active", "bot")
