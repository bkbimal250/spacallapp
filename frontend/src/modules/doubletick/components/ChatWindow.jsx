import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, Bot, CheckCheck, Clock3, Headphones, UserRound } from 'lucide-react';
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

    const getBubbleClass = (message, isInbound) => {
        if (message.status === 'failed') return 'bg-danger/10 border-danger/50 text-text-primary';
        if (isInbound) return 'bg-card border-border text-text-primary';
        if (message.origin === 'bot' || message.origin === 'api' || message.origin === 'system') return 'bg-info/10 border-info/30 text-text-primary';
        return 'bg-primary text-white border-primary';
    };

    const getMetaClass = (message, isInbound) => {
        if (!isInbound && message.status !== 'failed' && !['bot', 'api', 'system'].includes(message.origin)) return 'text-white/80';
        return 'text-text-secondary';
    };

    return (
        <div className="bg-background border border-border rounded-lg overflow-hidden">
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
            <div className="h-[520px] overflow-y-auto custom-scrollbar p-4 space-y-3 bg-gradient-to-b from-background to-card/30">
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
                        const bubbleClass = getBubbleClass(message, isInbound);
                        const metaClass = getMetaClass(message, isInbound);
                        const selectedReply = message.callback_data
                            || message.interactive_payload?.button_reply?.title
                            || message.interactive_payload?.list_reply?.title
                            || message.interactive_payload?.selected_title;
                        return (
                            <div key={message.id} className={`flex ${isInbound ? 'justify-start' : 'justify-end'}`}>
                                <div className={`max-w-[78%] rounded-2xl border px-4 py-3 shadow-sm ${bubbleClass}`}>
                                    <div className="flex flex-wrap items-center gap-2 mb-1">
                                        <Icon size={14} />
                                        <span className="text-xs font-semibold uppercase">{sender.type || message.origin || message.direction}</span>
                                        <span className={`text-xs font-medium ${metaClass}`}>
                                            {sender.name || message.sender_display_name || message.sent_by_name || 'Unknown'}
                                        </span>
                                    </div>
                                    <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">{message.text || message.caption || message.message_type}</p>
                                    {selectedReply && (
                                        <div className={`mt-2 rounded-lg border px-3 py-2 text-xs font-semibold ${isInbound ? 'border-primary/20 bg-primary/5 text-primary' : 'border-white/20'}`}>
                                            Selected reply: {selectedReply}
                                        </div>
                                    )}
                                    {message.message_type && message.message_type !== 'text' && (
                                        <div className={`mt-2 rounded-md border px-2 py-1 text-[11px] ${isInbound ? 'border-border' : 'border-white/20'}`}>
                                            Payload type: {message.message_type}
                                        </div>
                                    )}
                                    <div className={`flex flex-wrap items-center gap-2 text-[11px] mt-2 ${metaClass}`}>
                                        <span>{formatDate(timestamp, 'MMM dd, HH:mm')}</span>
                                        {status && (
                                            <span className="inline-flex items-center gap-1">
                                                {message.status === 'failed' ? <AlertCircle size={12} /> : message.status === 'queued' ? <Clock3 size={12} /> : <CheckCheck size={12} />}
                                                {status}
                                            </span>
                                        )}
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
