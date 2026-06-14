import React from 'react';
import {
    AlertCircle,
    CheckCircle2,
    Clock,
    Inbox,
    MapPin,
    MessageCircle,
    PhoneCall,
    Send,
    UserCheck,
} from 'lucide-react';

const metricConfig = [
    ['new_conversations_today', 'New Today', Inbox, 'text-primary'],
    ['greeting_only_conversations', 'Greetings', MessageCircle, 'text-info'],
    ['awaiting_location', 'Awaiting Location', MapPin, 'text-warning'],
    ['awaiting_customer', 'Awaiting Customer', Clock, 'text-warning'],
    ['manual_attention_required', 'Manual Attention', AlertCircle, 'text-danger'],
    ['unmatched_area', 'Unmatched Area', MapPin, 'text-danger'],
    ['qualified_leads', 'Qualified', CheckCircle2, 'text-success'],
    ['available_leads', 'Available', Send, 'text-primary'],
    ['claimed_leads', 'Claimed', UserCheck, 'text-info'],
    ['contacted_leads', 'Contacted', PhoneCall, 'text-success'],
    ['booked_leads', 'Booked', CheckCircle2, 'text-success'],
    ['lost_leads', 'Lost', AlertCircle, 'text-danger'],
];

const DoubleTickMetricGrid = ({ metrics = {}, loading = false }) => (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {metricConfig.map(([key, label, MetricIcon, color]) => (
            <div key={key} className="bg-card border border-border rounded-lg p-4 flex items-center gap-3 min-h-[88px]">
                <div className="bg-background border border-border rounded-lg p-2">
                    {React.createElement(MetricIcon, { size: 20, className: color })}
                </div>
                <div>
                    <p className="text-xs uppercase text-text-secondary font-semibold">{label}</p>
                    <p className="text-2xl font-bold text-text-primary">{loading ? '...' : metrics?.[key] ?? 0}</p>
                </div>
            </div>
        ))}
    </div>
);

export default DoubleTickMetricGrid;
