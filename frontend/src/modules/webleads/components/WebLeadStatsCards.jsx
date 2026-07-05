import React from 'react';
import { AlertTriangle, BellOff, CalendarDays, CheckCircle2, Clock, CopyX, ListChecks, TrendingUp } from 'lucide-react';

const metricMap = [
    ['total_website_leads', 'Total Website Leads', ListChecks],
    ['today_website_leads', 'Today Leads', CalendarDays],
    ['weekly_website_leads', 'This Week Leads', TrendingUp],
    ['monthly_website_leads', 'This Month Leads', Clock],
    ['converted_leads', 'Converted Leads', CheckCircle2],
    ['pending_unassigned_leads', 'Pending/Unassigned', AlertTriangle],
    ['duplicate_leads', 'Duplicate Leads', CopyX],
    ['notification_failed_count', 'Notification Failed', BellOff],
];

const WebLeadStatsCards = ({ stats = {} }) => (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metricMap.map(([key, label, Icon]) => (
            <div key={key} className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-center justify-between gap-3">
                    <div>
                        <p className="text-xs font-semibold uppercase text-text-secondary">{label}</p>
                        <p className="mt-2 text-2xl font-semibold text-text-primary">{stats[key] ?? stats[key.replace('_count', '')] ?? 0}</p>
                    </div>
                    <span className="rounded-lg bg-primary/10 p-2 text-primary">
                        <Icon size={20} />
                    </span>
                </div>
            </div>
        ))}
    </div>
);

export default WebLeadStatsCards;
