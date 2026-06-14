import React, { useEffect, useState } from 'react';
import { Archive, Flag, MapPin, RefreshCw, UserPlus, XCircle } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { doubletickAPI } from '../api';
import ChatWindow from './ChatWindow';
import ReplyPanel from './ReplyPanel';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import AreaMatchModal from './AreaMatchModal';

const ConversationDetailModal = ({ conversationId, isOpen, onClose, onChanged }) => {
    const [conversation, setConversation] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [matchOpen, setMatchOpen] = useState(false);
    const [actionLoading, setActionLoading] = useState('');

    const load = async () => {
        if (!conversationId) return;
        setLoading(true);
        try {
            const [detail, chat] = await Promise.all([
                doubletickAPI.getConversation(conversationId),
                doubletickAPI.getConversationMessages(conversationId),
            ]);
            setConversation(detail.data);
            setMessages(chat.data.results || chat.data || []);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen, conversationId]);

    const runAction = async (name, fn) => {
        setActionLoading(name);
        try {
            await fn();
            await load();
            onChanged?.();
        } catch (error) {
            alert(error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || error.message || 'Action failed.');
        } finally {
            setActionLoading('');
        }
    };

    return (
        <>
            <Modal isOpen={isOpen} onClose={onClose} title="WhatsApp Conversation">
                {loading || !conversation ? (
                    <div className="py-16 text-center text-text-secondary">Loading conversation...</div>
                ) : (
                    <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
                        <div className="space-y-4">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                    <h2 className="text-lg font-semibold">{conversation.customer_name || conversation.phone_number || 'Customer'}</h2>
                                    <p className="text-sm text-text-secondary">{conversation.phone_number || conversation.normalized_phone}</p>
                                </div>
                                <DoubleTickStatusBadge status={conversation.status} />
                            </div>
                            <ChatWindow messages={messages} loading={loading} />
                            <ReplyPanel
                                onReply={(data) => runAction('reply', () => doubletickAPI.replyToConversation(conversation.id, data))}
                                onRequestLocation={() => runAction('location', () => doubletickAPI.requestLocation(conversation.id))}
                                disabled={Boolean(actionLoading)}
                            />
                        </div>
                        <aside className="space-y-4">
                            <div className="bg-background border border-border rounded-lg p-4 space-y-2 text-sm">
                                <p><span className="text-text-secondary">Area:</span> {conversation.matched_area_name || conversation.raw_area || '-'}</p>
                                <p><span className="text-text-secondary">City:</span> {conversation.raw_city || '-'}</p>
                                <p><span className="text-text-secondary">Service:</span> {conversation.raw_service || '-'}</p>
                                <p><span className="text-text-secondary">Reason:</span> {conversation.pending_reason || '-'}</p>
                                <p><span className="text-text-secondary">Unread:</span> {conversation.unread_count || 0}</p>
                            </div>
                            <div className="grid grid-cols-1 gap-2">
                                <Button variant="secondary" className="gap-2 justify-start" onClick={() => setMatchOpen(true)}>
                                    <MapPin size={16} />
                                    Match Area
                                </Button>
                                <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'sync'} onClick={() => runAction('sync', () => doubletickAPI.syncConversationChat(conversation.id))}>
                                    <RefreshCw size={16} />
                                    Sync Chat
                                </Button>
                                <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'qualify'} onClick={() => runAction('qualify', () => doubletickAPI.qualifyConversation(conversation.id))}>
                                    <UserPlus size={16} />
                                    Qualify Lead
                                </Button>
                                <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'spam'} onClick={() => runAction('spam', () => doubletickAPI.markSpam(conversation.id))}>
                                    <Flag size={16} />
                                    Mark Spam
                                </Button>
                                <Button variant="danger" className="gap-2 justify-start" loading={actionLoading === 'close'} onClick={() => runAction('close', () => doubletickAPI.closeConversation(conversation.id))}>
                                    <Archive size={16} />
                                    Close
                                </Button>
                            </div>
                            {actionLoading && (
                                <div className="flex items-center gap-2 text-sm text-text-secondary">
                                    <XCircle size={14} />
                                    Working on {actionLoading}
                                </div>
                            )}
                        </aside>
                    </div>
                )}
            </Modal>
            <AreaMatchModal
                isOpen={matchOpen}
                conversation={conversation}
                onClose={() => setMatchOpen(false)}
                onSubmit={(data) => runAction('match', () => doubletickAPI.matchArea(conversation.id, data))}
            />
        </>
    );
};

export default ConversationDetailModal;
