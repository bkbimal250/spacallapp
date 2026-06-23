from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BotApiCallLogViewSet,
    BotDataSourceViewSet,
    BotExecutionLogViewSet,
    BotFallbackRuleViewSet,
    BotFlowViewSet,
    BotHandoverRuleViewSet,
    BotIntegrationViewSet,
    BotMessageTemplateViewSet,
    BotNodeOptionViewSet,
    BotNodeViewSet,
    BotSessionVariableViewSet,
    BotSessionViewSet,
    BotSheetSyncLogViewSet,
    BotTestFlowViewSet,
    BotTransitionViewSet,
    BotTriggerViewSet,
    BotViewSet,
)


router = DefaultRouter()
router.register("bots", BotViewSet, basename="bot")
router.register("flows", BotFlowViewSet, basename="bot-flow")
router.register("nodes", BotNodeViewSet, basename="bot-node")
router.register("node-options", BotNodeOptionViewSet, basename="bot-node-option")
router.register("transitions", BotTransitionViewSet, basename="bot-transition")
router.register("triggers", BotTriggerViewSet, basename="bot-trigger")
router.register("sessions", BotSessionViewSet, basename="bot-session")
router.register("session-variables", BotSessionVariableViewSet, basename="bot-session-variable")
router.register("execution-logs", BotExecutionLogViewSet, basename="bot-execution-log")
router.register("message-templates", BotMessageTemplateViewSet, basename="bot-message-template")
router.register("data-sources", BotDataSourceViewSet, basename="bot-data-source")
router.register("integrations", BotIntegrationViewSet, basename="bot-integration")
router.register("api-call-logs", BotApiCallLogViewSet, basename="bot-api-call-log")
router.register("sheet-sync-logs", BotSheetSyncLogViewSet, basename="bot-sheet-sync-log")
router.register("handover-rules", BotHandoverRuleViewSet, basename="bot-handover-rule")
router.register("fallback-rules", BotFallbackRuleViewSet, basename="bot-fallback-rule")
router.register("test-flow", BotTestFlowViewSet, basename="bot-test-flow")

urlpatterns = [
    path("", include(router.urls)),
]
