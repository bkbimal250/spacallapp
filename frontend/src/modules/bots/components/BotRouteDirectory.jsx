import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, Braces, Cable, Database, GitFork, ListChecks, MessageSquareText, Route, ShieldAlert, Split, Workflow } from 'lucide-react';
import { ROUTES } from '../../../routes/routeConfig';

const groups = [
    {
        title: 'Design',
        links: [
            { to: ROUTES.BOTS_BUILDER, label: 'Workflow Builder', icon: Workflow },
            { to: ROUTES.BOTS_FLOWS, label: 'Flows', icon: GitFork },
            { to: ROUTES.BOTS_NODES, label: 'Nodes', icon: Route },
            { to: ROUTES.BOTS_NODE_OPTIONS, label: 'Node Options', icon: ListChecks },
            { to: ROUTES.BOTS_TRANSITIONS, label: 'Transitions', icon: Split },
        ],
    },
    {
        title: 'Automation',
        links: [
            { to: ROUTES.BOTS_TRIGGERS, label: 'Triggers', icon: Activity },
            { to: ROUTES.BOTS_TEMPLATES, label: 'Templates', icon: MessageSquareText },
            { to: ROUTES.BOTS_DATA_SOURCES, label: 'Data Sources', icon: Database },
            { to: ROUTES.BOTS_HANDOVER_RULES, label: 'Handover Rules', icon: ShieldAlert },
            { to: ROUTES.BOTS_FALLBACK_RULES, label: 'Fallback Rules', icon: ShieldAlert },
        ],
    },
    {
        title: 'Runtime',
        links: [
            { to: ROUTES.BOTS_SESSIONS, label: 'Sessions', icon: GitFork },
            { to: ROUTES.BOTS_SESSION_VARIABLES, label: 'Session Variables', icon: Braces },
            { to: ROUTES.BOTS_LOGS, label: 'Execution Logs', icon: Braces },
            { to: ROUTES.BOTS_API_CALL_LOGS, label: 'API Call Logs', icon: Cable },
            { to: ROUTES.BOTS_SHEET_SYNC_LOGS, label: 'Sheet Sync Logs', icon: Database },
            { to: ROUTES.BOTS_INTEGRATIONS, label: 'Integrations', icon: Cable },
            { to: ROUTES.BOTS_SIMULATOR, label: 'Simulator', icon: Workflow },
        ],
    },
];

const BotRouteDirectory = () => (
    <section className="rounded-lg border border-border bg-card p-4">
        <div className="mb-4">
            <h2 className="font-semibold text-text-primary">Bot Workflow Routes</h2>
            <p className="text-sm text-text-secondary">Open each bot workflow area as a separate page.</p>
        </div>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            {groups.map((group) => (
                <div key={group.title} className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-text-secondary">{group.title}</p>
                    <div className="grid gap-2">
                        {group.links.map((item) => (
                            <Link
                                key={item.to}
                                to={item.to}
                                className="flex items-center gap-3 rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary transition hover:border-primary/50 hover:bg-cardHover"
                            >
                                <item.icon size={16} className="text-primary" />
                                <span className="font-medium">{item.label}</span>
                            </Link>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    </section>
);

export default BotRouteDirectory;
