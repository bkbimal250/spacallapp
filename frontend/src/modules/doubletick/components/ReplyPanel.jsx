import React, { useState } from 'react';
import { MapPin, Send, MessageSquare } from 'lucide-react';
import Button from '../../../shared/components/Button';
import { formatDate } from '../../../shared/utils/formatDate';

const ReplyPanel = ({ onReply, onRequestLocation, disabled = false, lastLocationRequestAt = null }) => {
    const [text, setText] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const submit = async () => {
        if (!text.trim()) return;
        setSubmitting(true);
        try {
            await onReply({ message_type: 'text', text });
            setText('');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="border border-border rounded-lg p-4 bg-card space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <MessageSquare size={16} />
                Manual WhatsApp Reply
            </div>
            <textarea
                className="w-full min-h-[100px] bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary resize-none"
                placeholder="Type your WhatsApp message here... (supports multi-line)"
                value={text}
                disabled={disabled || submitting}
                onChange={(event) => setText(event.target.value)}
            />
            <div className="flex flex-wrap justify-between gap-2">
                <Button type="button" variant="secondary" className="gap-2" disabled={disabled || submitting} onClick={onRequestLocation}>
                    <MapPin size={16} />
                    Request Location
                </Button>
                <Button type="button" className="gap-2" loading={submitting} disabled={disabled || !text.trim()} onClick={submit}>
                    <Send size={16} />
                    Send Reply
                </Button>
            </div>
            {lastLocationRequestAt && (
                <p className="text-xs text-text-secondary">Last location request: {formatDate(lastLocationRequestAt, 'MMM dd, HH:mm')}</p>
            )}
        </div>
    );
};

export default ReplyPanel;
