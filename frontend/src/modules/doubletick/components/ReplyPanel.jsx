import React, { useState } from 'react';
import { MapPin, Send } from 'lucide-react';
import Button from '../../../shared/components/Button';

const ReplyPanel = ({ onReply, onRequestLocation, disabled = false }) => {
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
        <div className="border border-border rounded-lg p-3 bg-card space-y-3">
            <textarea
                className="w-full min-h-[88px] bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary resize-none"
                placeholder="Type a manual WhatsApp reply"
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
                    Reply
                </Button>
            </div>
        </div>
    );
};

export default ReplyPanel;
