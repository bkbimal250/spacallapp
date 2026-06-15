import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Bot, Headphones, UserRound } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';

const originIcon = {
    customer: UserRound,
    agent: Headphones,
    bot: Bot,
    api: Bot,
    system: Bot,
};

const statusLabels = {
    received: 'Received',
    queued: 'Sending',
    sent: 'Sent',
    delivered: 'Delivered',
    read: 'Read',
    failed: 'Failed',
};

const filters = [
    { key: 'all', label: 'All' },
    { key: 'customer', label: 'Customer' },
    { key: 'associate', label: 'Associate' },
    { key: 'automation', label: 'Bot/API' },
    { key: 'failed', label: 'Failed' },
];

const ChatWindow = ({ messages = [], loading = false }) => {
    const bottomRef = useRef(null);
    const [filter, setFilter] = useState('all');

    const visibleMessages = useMemo(() => {
        return messages.filter((message) => {
            if (filter === 'customer') return message.direction === 'inbound' || message.origin === 'customer';
            if (filter === 'associate') return message.origin === 'agent';
            if (filter === 'automation') return ['bot', 'api', 'system'].includes(message.origin);
            if (filter === 'failed') return message.status === 'failed';
            return true;
        });
    }, [filter, messages]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [visibleMessages]);

    if (loading) {
        return <div className="p-6 text-center text-text-secondary">Loading chat...</div>;
    }

    return (
        <div className="bg-background border border-border rounded-lg">
            <div className="flex flex-wrap gap-2 border-b border-border p-3">
                {filters.map((item) => (
                    <button
                        key={item.key}
                        type="button"
                        onClick={() => setFilter(item.key)}
                        className={`px-3 py-1 rounded-md text-xs border ${filter === item.key ? 'bg-primary text-white border-primary' : 'border-border text-text-secondary hover:text-text-primary'}`}
                    >
                        {item.label}
                    </button>
                ))}
            </div>
            <div className="h-[460px] overflow-y-auto custom-scrollbar p-4 space-y-3">
                {messages.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-text-secondary">No messages have been synchronized yet.</div>
                ) : visibleMessages.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-text-secondary">No messages match this filter.</div>
                ) : (
                    visibleMessages.map((message) => {
                        const isInbound = message.direction === 'inbound';
                        const Icon = originIcon[message.origin] || Bot;
                        const sender = message.sender || {};
                        const status = statusLabels[message.status] || message.status;
                        const timestamp = message.timestamp || message.message_timestamp || message.received_at || message.sent_at || message.created_at;
                        return (
                            <div key={message.id} className={`flex ${isInbound ? 'justify-start' : 'justify-end'}`}>
                                <div className={`max-w-[78%] rounded-lg border px-4 py-3 ${isInbound ? 'bg-card border-border' : message.status === 'failed' ? 'bg-danger/10 border-danger text-text-primary' : 'bg-primary text-white border-primary'}`}>
                                    <div className="flex flex-wrap items-center gap-2 mb-1">
                                        <Icon size={14} />
                                        <span className="text-xs font-semibold uppercase">{sender.type || message.origin || message.direction}</span>
                                        <span className={`text-xs font-medium ${isInbound || message.status === 'failed' ? 'text-text-primary' : 'text-white'}`}>
                                            {sender.name || message.sender_display_name || message.sent_by_name || 'Unknown'}
                                        </span>
                                    </div>
                                    <p className="text-sm whitespace-pre-wrap break-words">{message.text || message.caption || message.message_type}</p>
                                    <div className={`flex flex-wrap items-center gap-2 text-[11px] mt-2 ${isInbound || message.status === 'failed' ? 'text-text-secondary' : 'text-white/80'}`}>
                                        <span>{formatDate(timestamp, 'MMM dd, HH:mm')}</span>
                                        {status && <span>{status}</span>}
                                    </div>
                                    {message.status === 'failed' && message.failure_reason && (
                                        <p className="text-[11px] mt-1 text-danger break-words">{message.failure_reason}</p>
                                    )}
                                </div>
                            </div>
                        );
                    })
                )}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default ChatWindow;
