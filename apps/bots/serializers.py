from rest_framework import serializers

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


class BotSerializer(serializers.ModelSerializer):
    active_flow_id = serializers.SerializerMethodField()

    class Meta:
        model = Bot
        fields = "__all__"

    def get_active_flow_id(self, obj):
        flow = obj.flows.filter(is_active=True).order_by("-version").first()
        return str(flow.id) if flow else None


class BotFlowSerializer(serializers.ModelSerializer):
    bot_name = serializers.CharField(source="bot.name", read_only=True)

    class Meta:
        model = BotFlow
        fields = "__all__"


class BotNodeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotNodeOption
        fields = "__all__"


class BotNodeSerializer(serializers.ModelSerializer):
    options = BotNodeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = BotNode
        fields = "__all__"


class BotTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotTransition
        fields = "__all__"


class BotTriggerSerializer(serializers.ModelSerializer):
    bot_name = serializers.CharField(source="bot.name", read_only=True)
    channel_name = serializers.CharField(source="channel.name", read_only=True)
    branch_name = serializers.CharField(source="branch.spa_name", read_only=True)

    class Meta:
        model = BotTrigger
        fields = "__all__"


class BotSessionVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotSessionVariable
        fields = "__all__"


class BotSessionSerializer(serializers.ModelSerializer):
    bot_name = serializers.CharField(source="bot.name", read_only=True)
    current_node_name = serializers.CharField(source="current_node.name", read_only=True)
    selected_branch_name = serializers.CharField(source="selected_branch.spa_name", read_only=True)

    class Meta:
        model = BotSession
        fields = "__all__"


class BotExecutionLogSerializer(serializers.ModelSerializer):
    bot_name = serializers.CharField(source="session.bot.name", read_only=True)
    node_name = serializers.CharField(source="node.name", read_only=True)

    class Meta:
        model = BotExecutionLog
        fields = "__all__"


class BotMessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotMessageTemplate
        fields = "__all__"


class BotDataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotDataSource
        fields = "__all__"


class BotIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotIntegration
        fields = "__all__"


class BotApiCallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotApiCallLog
        fields = "__all__"


class BotSheetSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotSheetSyncLog
        fields = "__all__"


class BotHandoverRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotHandoverRule
        fields = "__all__"


class BotFallbackRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotFallbackRule
        fields = "__all__"


class BotTestFlowSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(required=False)
    lead_id = serializers.UUIDField(required=False)
    text = serializers.CharField(required=False, allow_blank=True)
    node_id = serializers.UUIDField(required=False)


class BotRunNodeSerializer(serializers.Serializer):
    node_id = serializers.UUIDField()
    text = serializers.CharField(required=False, allow_blank=True)
