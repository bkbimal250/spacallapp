import React, { useEffect, useRef } from 'react';
import { Bot, Headphones, UserRound } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';

const originIcon = {
    customer: UserRound,
    agent: Headphones,
    bot: Bot,
    api: Bot,
    system: Bot,
};

const ChatWindow = ({ messages = [], loading = false }) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    if (loading) {
        return <div className="p-6 text-center text-text-secondary">Loading chat...</div>;
    }

    return (
        <div className="h-[460px] overflow-y-auto custom-scrollbar bg-background border border-border rounded-lg p-4 space-y-3">
            {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-text-secondary">No messages stored yet.</div>
            ) : (
                messages.map((message) => {
                    const isInbound = message.direction === 'inbound';
                    const Icon = originIcon[message.origin] || Bot;
                    return (
                        <div key={message.id} className={`flex ${isInbound ? 'justify-start' : 'justify-end'}`}>
                            <div className={`max-w-[78%] rounded-lg border px-4 py-3 ${isInbound ? 'bg-card border-border' : 'bg-primary text-white border-primary'}`}>
                                <div className="flex items-center gap-2 mb-1">
                                    <Icon size={14} />
                                    <span className="text-xs font-semibold uppercase">{message.origin || message.direction}</span>
                                    <span className={`text-[11px] ${isInbound ? 'text-text-secondary' : 'text-white/80'}`}>
                                        {formatDate(message.received_at || message.sent_at || message.created_at, 'MMM dd, HH:mm')}
                                    </span>
                                </div>
                                <p className="text-sm whitespace-pre-wrap break-words">{message.text || message.caption || message.message_type}</p>
                                {message.status && (
                                    <p className={`text-[11px] mt-2 ${isInbound ? 'text-text-secondary' : 'text-white/80'}`}>{message.status}</p>
                                )}
                            </div>
                        </div>
                    );
                })
            )}
            <div ref={bottomRef} />
        </div>
    );
};

export default ChatWindow;
