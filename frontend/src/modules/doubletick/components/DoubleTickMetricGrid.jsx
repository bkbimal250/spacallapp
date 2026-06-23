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
    ['new_conversations_today', 'New Today', Inbox, 'text-primary', 'New conversations arrived'],
    ['greeting_only_conversations', 'Greetings', MessageCircle, 'text-info', 'Greeting-only messages'],
    ['awaiting_location', 'Awaiting Location', MapPin, 'text-warning', 'No location data'],
    ['awaiting_customer', 'Awaiting Customer', Clock, 'text-warning', 'Waiting for customer reply'],
    ['manual_attention_required', 'Manual Attention', AlertCircle, 'text-danger', 'Need CRM review'],
    ['unmatched_area', 'Unmatched Area', MapPin, 'text-danger', 'Can\'t match to CRM area'],
    ['qualified_leads', 'Qualified', CheckCircle2, 'text-success', 'Ready to distribute'],
    ['available_leads', 'Available', Send, 'text-primary', 'Can be claimed by branch'],
    ['claimed_leads', 'Claimed', UserCheck, 'text-info', 'Already have an owner'],
    ['contacted_leads', 'Contacted', PhoneCall, 'text-success', 'Owner reached out'],
    ['booked_leads', 'Booked', CheckCircle2, 'text-success', 'Booking confirmed'],
    ['lost_leads', 'Lost', AlertCircle, 'text-danger', 'Lost opportunity'],
];

const DoubleTickMetricGrid = ({ metrics = {}, loading = false }) => (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {metricConfig.map(([key, label, MetricIcon, color, tooltip]) => (
            <div key={key} className="bg-card border border-border rounded-lg p-4 flex items-center gap-3 min-h-[100px] hover:border-primary/50 transition group cursor-help" title={tooltip}>
                <div className="bg-background border border-border rounded-lg p-2 group-hover:bg-primary/5 transition">
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
