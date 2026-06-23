import React from 'react';
import { AlertTriangle, CheckCircle2, GitFork, MessageSquareText, PlugZap, Workflow } from 'lucide-react';

const metricsConfig = [
    ['total_bot_sessions', 'Total Sessions', GitFork, 'text-primary'],
    ['active_sessions', 'Active', Workflow, 'text-info'],
    ['completed_sessions', 'Completed', CheckCircle2, 'text-success'],
    ['handed_over_sessions', 'Handed Over', AlertTriangle, 'text-warning'],
    ['bot_messages_sent', 'Bot Messages', MessageSquareText, 'text-primary'],
    ['api_failures', 'API Failures', PlugZap, 'text-danger'],
];

const BotMetricGrid = ({ metrics = {}, loading = false }) => (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {metricsConfig.map(([key, label, icon, color]) => {
            const metricIcon = React.createElement(icon, { size: 20, className: color });
            return (
                <div key={key} className="bg-card border border-border rounded-lg p-4 flex items-center gap-3 min-h-[88px]">
                    <div className="bg-background border border-border rounded-lg p-2">
                        {metricIcon}
                    </div>
                    <div>
                        <p className="text-xs uppercase text-text-secondary font-semibold">{label}</p>
                        <p className="text-2xl font-bold text-text-primary">{loading ? '...' : metrics?.[key] ?? 0}</p>
                    </div>
                </div>
            );
        })}
    </div>
);

export default BotMetricGrid;
