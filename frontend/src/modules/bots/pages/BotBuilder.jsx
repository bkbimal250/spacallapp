import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Bot, Braces, GitFork, ListTree, MessageSquareText, RefreshCw, Settings2, Workflow } from 'lucide-react';
import Button from '../../../shared/components/Button';
import BotListPanel from '../components/BotListPanel';
import BotFormModal from '../components/BotFormModal';
import BotMetricGrid from '../components/BotMetricGrid';
import BotStatusBadge from '../components/BotStatusBadge';
import BotRouteDirectory from '../components/BotRouteDirectory';
import FlowDesigner from '../components/FlowDesigner';
import { botsAPI } from '../api';
import { formatLabel, getList, nodeTypeGroups } from '../utils';

const nodeTone = {
    start: 'bg-success/10 text-success border-success/20',
    question: 'bg-primary/10 text-primary border-primary/20',
    dynamic_city_select: 'bg-info/10 text-info border-info/20',
    dynamic_area_select: 'bg-info/10 text-info border-info/20',
    dynamic_branch_select: 'bg-info/10 text-info border-info/20',
    api_call: 'bg-warning/10 text-warning border-warning/20',
    google_sheet_append: 'bg-warning/10 text-warning border-warning/20',
    manual_handover: 'bg-danger/10 text-danger border-danger/20',
    fallback: 'bg-danger/10 text-danger border-danger/20',
    end: 'bg-text-secondary/10 text-text-secondary border-border',
};

const Panel = ({ icon: Icon, title, action, children }) => (
    <section className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
                {Icon && <Icon size={18} className="text-primary" />}
                <h2 className="font-semibold text-text-primary">{title}</h2>
            </div>
            {action}
        </div>
        <div className="p-4">{children}</div>
    </section>
);

const pageCopy = {
    overview: {
        title: 'WhatsApp Bot Overview',
        description: 'Monitor bot coverage, active sessions, and execution health.',
    },
    builder: {
        title: 'WhatsApp Bot Workflow Builder',
        description: 'Design full bot routes with enough canvas space for city, area, branch, handover, and lead assignment paths.',
    },
    sessions: {
        title: 'Bot Sessions',
        description: 'Review active and completed WhatsApp bot conversations.',
    },
    logs: {
        title: 'Bot Execution Logs',
        description: 'Inspect bot events, node execution, and errors.',
    },
    integrations: {
        title: 'Bot Integrations',
        description: 'Manage connected systems used by bot workflows.',
    },
};

const BotBuilder = ({ activeView = 'overview' }) => {
    const [metrics, setMetrics] = useState({});
    const [bots, setBots] = useState([]);
    const [selectedBot, setSelectedBot] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [logs, setLogs] = useState([]);
    const [integrations, setIntegrations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [createOpen, setCreateOpen] = useState(false);
    const [createLoading, setCreateLoading] = useState(false);
    const [createError, setCreateError] = useState('');
    const [createSuccess, setCreateSuccess] = useState('');

    const loadBots = useCallback(async () => {
        setLoading(true);
        try {
            const [statsRes, botsRes] = await Promise.all([
                botsAPI.getStats().catch(() => ({ data: {} })),
                botsAPI.getBots({ all: true }),
            ]);
            const botList = getList(botsRes);
            setMetrics(statsRes.data || {});
            setBots(botList);
            setSelectedBot((current) => botList.find((bot) => bot.id === current?.id) || botList[0] || null);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadBotWorkspace = useCallback(async (bot) => {
        if (!bot?.id) {
            setNodes([]);
            setSessions([]);
            setLogs([]);
            setIntegrations([]);
            return;
        }
        setDetailLoading(true);
        try {
            const [nodesRes, sessionsRes, logsRes, integrationsRes] = await Promise.all([
                botsAPI.getNodes({ bot: bot.id, all: true }).catch(() => ({ data: [] })),
                botsAPI.getSessions({ bot: bot.id, all: true }).catch(() => ({ data: [] })),
                botsAPI.getExecutionLogs({ bot: bot.id, all: true }).catch(() => ({ data: [] })),
                botsAPI.getIntegrations({ bot: bot.id, all: true }).catch(() => ({ data: [] })),
            ]);
            setNodes(getList(nodesRes));
            setSessions(getList(sessionsRes));
            setLogs(getList(logsRes));
            setIntegrations(getList(integrationsRes));
        } finally {
            setDetailLoading(false);
        }
    }, []);

    useEffect(() => {
        loadBots();
    }, [loadBots]);

    useEffect(() => {
        loadBotWorkspace(selectedBot);
    }, [loadBotWorkspace, selectedBot]);

    const nodesByType = useMemo(() => {
        return nodes.reduce((acc, node) => {
            acc[node.node_type] = (acc[node.node_type] || 0) + 1;
            return acc;
        }, {});
    }, [nodes]);

    const handleCreateBot = async (form) => {
        setCreateLoading(true);
        setCreateError('');
        setCreateSuccess('');
        try {
            const botPayload = {
                name: form.name.trim(),
                slug: form.slug.trim(),
                bot_type: form.bot_type,
                description: form.description || '',
                default_language: form.default_language || 'en',
                priority: Number(form.priority || 0),
                is_active: Boolean(form.is_active),
                config: form.config || {},
            };
            const botResponse = await botsAPI.createBot(botPayload);
            const createdBot = botResponse.data;

            if (form.trigger_type) {
                const keywords = String(form.keywords || '')
                    .split(',')
                    .map((item) => item.trim())
                    .filter(Boolean);
                const triggerPayload = {
                    bot: createdBot.id,
                    trigger_type: form.trigger_type,
                    keywords,
                    channel: form.channel || null,
                    source_campaign: form.source_campaign || '',
                    city: form.city || '',
                    lead_type: form.lead_type || '',
                    is_default: Boolean(form.is_default_trigger),
                    is_active: true,
                    priority: Number(form.trigger_priority || 0),
                    config: {},
                };
                await botsAPI.createTrigger(triggerPayload);
            }

            setCreateSuccess('Bot created successfully.');
            await loadBots();
            setSelectedBot(createdBot);
            setTimeout(() => {
                setCreateOpen(false);
                setCreateSuccess('');
            }, 700);
        } catch (error) {
            const data = error.response?.data;
            const message = typeof data === 'string'
                ? data
                : data?.detail
                    || data?.non_field_errors?.[0]
                    || Object.entries(data || {})[0]?.join(': ')
                    || error.message
                    || 'Failed to create bot.';
            setCreateError(message);
        } finally {
            setCreateLoading(false);
        }
    };

    const handleDeleteBot = async (bot) => {
        if (!bot?.id) return;
        if (!window.confirm(`Delete bot "${bot.name}"? This cannot be undone.`)) return;
        try {
            await botsAPI.deleteBot(bot.id);
            if (selectedBot?.id === bot.id) {
                setSelectedBot(null);
            }
            await loadBots();
        } catch (error) {
            console.error('Failed to delete bot', error);
            const message = error.response?.data?.detail || 'Failed to delete bot. It may be linked with sessions, flows, or triggers.';
            window.alert(message);
        }
    };

    const renderBotDetail = () => (
        <Panel icon={Bot} title="Bot Detail">
            {!selectedBot ? (
                <p className="text-sm text-text-secondary">Select a bot to inspect its flow.</p>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div className="md:col-span-2">
                        <p className="text-lg font-semibold text-text-primary">{selectedBot.name}</p>
                        <p className="text-sm text-text-secondary">{selectedBot.description || 'No description provided.'}</p>
                    </div>
                    <div>
                        <p className="text-xs uppercase font-semibold text-text-secondary">Type</p>
                        <p className="text-sm font-medium">{formatLabel(selectedBot.bot_type)}</p>
                    </div>
                    <div>
                        <p className="text-xs uppercase font-semibold text-text-secondary">Status</p>
                        <BotStatusBadge active={selectedBot.is_active} />
                    </div>
                </div>
            )}
        </Panel>
    );

    const renderNodes = () => (
        <Panel icon={Workflow} title="Flow Nodes" action={<span className="text-xs text-text-secondary">{detailLoading ? 'Loading...' : `${nodes.length} nodes`}</span>}>
            {nodes.length === 0 ? (
                <p className="text-sm text-text-secondary">No nodes found for this bot.</p>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                    {nodes.map((node) => (
                        <div key={node.id} className="border border-border rounded-lg p-3 bg-background">
                            <div className="flex items-start justify-between gap-2">
                                <div>
                                    <p className="font-semibold text-text-primary">{node.name || formatLabel(node.node_type)}</p>
                                    <span className={`inline-flex mt-1 rounded-md border px-2 py-0.5 text-xs font-semibold ${nodeTone[node.node_type] || 'bg-card text-text-secondary border-border'}`}>
                                        {formatLabel(node.node_type)}
                                    </span>
                                </div>
                                <span className="text-xs text-text-secondary">#{node.order ?? node.position ?? 0}</span>
                            </div>
                            <p className="text-sm text-text-secondary mt-2 line-clamp-3">{node.message_text || node.preview_text || 'No message text configured.'}</p>
                        </div>
                    ))}
                </div>
            )}
        </Panel>
    );

    const renderNodeCoverage = () => (
        <Panel icon={ListTree} title="Node Type Coverage">
            <div className="space-y-3">
                {nodeTypeGroups.map((group) => (
                    <div key={group.label}>
                        <p className="text-xs uppercase font-semibold text-text-secondary mb-2">{group.label}</p>
                        <div className="flex flex-wrap gap-2">
                            {group.items.map((type) => (
                                <span key={type} className={`rounded-md border px-2 py-1 text-xs ${nodesByType[type] ? 'border-primary/30 bg-primary/10 text-primary' : 'border-border text-text-secondary'}`}>
                                    {formatLabel(type)} {nodesByType[type] ? `(${nodesByType[type]})` : ''}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </Panel>
    );

    const renderSessions = (limit) => {
        const rows = limit ? sessions.slice(0, limit) : sessions;
        return (
            <Panel icon={GitFork} title={limit ? 'Recent Sessions' : 'Bot Sessions'} action={<span className="text-xs text-text-secondary">{rows.length} shown</span>}>
                <div className="space-y-2 max-h-[560px] overflow-y-auto custom-scrollbar">
                    {rows.length === 0 ? (
                        <p className="text-sm text-text-secondary">No sessions found.</p>
                    ) : rows.map((session) => (
                        <div key={session.id} className="grid gap-2 rounded-lg border border-border bg-background p-3 text-sm md:grid-cols-[1.2fr_1fr_1fr_auto]">
                            <div>
                                <p className="font-medium text-text-primary">{session.customer_name || session.customer_phone || session.customer || session.id}</p>
                                <p className="text-xs text-text-secondary">{session.customer_phone || session.phone_number || '-'}</p>
                            </div>
                            <div>
                                <p className="text-xs uppercase font-semibold text-text-secondary">Current Node</p>
                                <p className="text-sm text-text-primary">{session.current_node_name || session.current_node || 'No node'}</p>
                            </div>
                            <div>
                                <p className="text-xs uppercase font-semibold text-text-secondary">Location</p>
                                <p className="text-sm text-text-primary">{[session.selected_city, session.selected_area].filter(Boolean).join(', ') || '-'}</p>
                            </div>
                            <span className="self-start rounded-md border border-border px-2 py-1 text-xs font-semibold text-text-secondary">
                                {formatLabel(session.status)}
                            </span>
                        </div>
                    ))}
                </div>
            </Panel>
        );
    };

    const renderLogs = (limit) => {
        const rows = limit ? logs.slice(0, limit) : logs;
        return (
            <Panel icon={Braces} title={limit ? 'Execution Logs' : 'Bot Execution Logs'} action={<span className="text-xs text-text-secondary">{rows.length} shown</span>}>
                <div className="space-y-2 max-h-[560px] overflow-y-auto custom-scrollbar">
                    {rows.length === 0 ? (
                        <p className="text-sm text-text-secondary">No logs found.</p>
                    ) : rows.map((log) => (
                        <div key={log.id} className="grid gap-2 rounded-lg border border-border bg-background p-3 text-sm md:grid-cols-[1fr_1fr_1fr]">
                            <div>
                                <p className="font-medium text-text-primary">{formatLabel(log.event_type || log.event || log.action || log.status)}</p>
                                <p className="text-xs text-text-secondary">{log.created_at || log.timestamp || '-'}</p>
                            </div>
                            <div>
                                <p className="text-xs uppercase font-semibold text-text-secondary">Node / Session</p>
                                <p className="text-sm text-text-primary">{log.node_name || log.node || log.session || '-'}</p>
                            </div>
                            <div>
                                <p className="text-xs uppercase font-semibold text-text-secondary">Result</p>
                                <p className={`text-sm ${log.error_message ? 'text-danger' : 'text-text-primary'}`}>{log.error_message || log.message || log.detail || formatLabel(log.status)}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </Panel>
        );
    };

    const renderIntegrations = () => (
        <Panel icon={Settings2} title="Bot Integrations" action={<span className="text-xs text-text-secondary">{integrations.length} integrations</span>}>
            <div className="space-y-2">
                {integrations.length === 0 ? (
                    <p className="text-sm text-text-secondary">No integrations found for this bot.</p>
                ) : integrations.map((integration) => (
                    <div key={integration.id} className="grid gap-2 rounded-lg border border-border bg-background p-3 text-sm md:grid-cols-[1fr_1fr_auto]">
                        <div>
                            <p className="font-medium text-text-primary">{integration.name || formatLabel(integration.integration_type)}</p>
                            <p className="text-xs text-text-secondary">{formatLabel(integration.integration_type)}</p>
                        </div>
                        <p className="text-text-secondary">{integration.description || integration.endpoint_url || '-'}</p>
                        <BotStatusBadge active={integration.is_active} />
                    </div>
                ))}
            </div>
        </Panel>
    );

    const renderTabContent = () => {
        if (activeView === 'sessions') return renderSessions();
        if (activeView === 'logs') return renderLogs();
        if (activeView === 'integrations') return renderIntegrations();
        if (activeView === 'builder') {
            return (
                <FlowDesigner 
                    bot={selectedBot} 
                    onRefreshWorkspace={() => loadBotWorkspace(selectedBot)} 
                    spacious
                />
            );
        }
        return (
            <>
                <BotRouteDirectory />
                <BotMetricGrid metrics={metrics} loading={loading} />
                {renderBotDetail()}
                <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-5">
                    {renderNodes()}
                    {renderNodeCoverage()}
                </div>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                    {renderSessions(8)}
                    {renderLogs(8)}
                </div>
                <Panel icon={MessageSquareText} title="Configuration Notes">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                        <div className="rounded-lg border border-border bg-background p-3">
                            <p className="font-semibold text-text-primary">City to Area to Branch</p>
                            <p className="text-text-secondary mt-1">Use dynamic city, area, and branch nodes for database-backed location selection.</p>
                        </div>
                        <div className="rounded-lg border border-border bg-background p-3">
                            <p className="font-semibold text-text-primary">Manual Handover</p>
                            <p className="text-text-secondary mt-1">Fallback and handover nodes should route unclear messages to the pending queue.</p>
                        </div>
                        <div className="rounded-lg border border-border bg-background p-3">
                            <p className="font-semibold text-text-primary">Integrations</p>
                            <p className="text-text-secondary mt-1">API and Google Sheet nodes remain visible in coverage for connector setup.</p>
                        </div>
                    </div>
                </Panel>
            </>
        );
    };

    const copy = pageCopy[activeView] || pageCopy.overview;

    if (activeView === 'builder') {
        return (
            <div className="space-y-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-bold text-text-primary">{copy.title}</h1>
                        <p className="text-sm text-text-secondary">{copy.description}</p>
                    </div>
                    <Button type="button" variant="secondary" className="gap-2" onClick={loadBots}>
                        <RefreshCw size={16} />
                        Refresh
                    </Button>
                </div>

                <div className="bg-card border border-border rounded-lg px-4 py-3 flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-[260px] flex-1">
                        <label className="block text-xs font-semibold uppercase tracking-wide text-text-secondary mb-1">Active Bot</label>
                        <select
                            className="w-full max-w-xl px-3 py-2 rounded-lg border border-border bg-background text-sm text-text-primary"
                            value={selectedBot?.id || ''}
                            onChange={(event) => {
                                const bot = bots.find((item) => String(item.id) === String(event.target.value));
                                setSelectedBot(bot || null);
                            }}
                        >
                            {bots.length === 0 ? (
                                <option value="">No bots available</option>
                            ) : bots.map((bot) => (
                                <option key={bot.id} value={bot.id}>
                                    {bot.name} - {formatLabel(bot.bot_type)}
                                </option>
                            ))}
                        </select>
                    </div>
                    <Button
                        type="button"
                        onClick={() => {
                            setCreateError('');
                            setCreateSuccess('');
                            setCreateOpen(true);
                        }}
                    >
                        Create Bot
                    </Button>
                </div>

                <FlowDesigner
                    bot={selectedBot}
                    onRefreshWorkspace={() => loadBotWorkspace(selectedBot)}
                    spacious
                />

                <BotFormModal
                    isOpen={createOpen}
                    onClose={() => setCreateOpen(false)}
                    onSubmit={handleCreateBot}
                    submitting={createLoading}
                    error={createError}
                    success={createSuccess}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">{copy.title}</h1>
                    <p className="text-sm text-text-secondary">{copy.description}</p>
                </div>
                <Button type="button" variant="secondary" className="gap-2" onClick={loadBots}>
                    <RefreshCw size={16} />
                    Refresh
                </Button>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr] gap-5">
                <BotListPanel
                    bots={bots}
                    selectedBotId={selectedBot?.id}
                    loading={loading}
                    onSelect={setSelectedBot}
                    onRefresh={loadBots}
                    onCreate={() => {
                        setCreateError('');
                        setCreateSuccess('');
                        setCreateOpen(true);
                    }}
                    onClone={(bot) => botsAPI.cloneBot(bot.id, { name: `${bot.name} Copy` }).then(loadBots)}
                    onDelete={handleDeleteBot}
                />

                <div className="space-y-5">
                    {renderTabContent()}
                </div>
            </div>
            <BotFormModal
                isOpen={createOpen}
                onClose={() => setCreateOpen(false)}
                onSubmit={handleCreateBot}
                submitting={createLoading}
                error={createError}
                success={createSuccess}
            />
        </div>
    );
};

export default BotBuilder;
