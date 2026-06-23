import React, { useEffect, useState } from 'react';
import { Archive, CheckCircle2, Flag, MapPin, Phone, RefreshCw, Send, UserPlus, XCircle } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { doubletickAPI } from '../api';
import ChatWindow from './ChatWindow';
import ReplyPanel from './ReplyPanel';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import AreaMatchModal from './AreaMatchModal';
import { customerName, customerPhone, leadArea, leadLocation, pendingReason, wabaNumber } from '../display';

const DetailPill = ({ label, value, tone = '' }) => (
    <div className={`rounded-lg border border-border bg-card/50 px-3 py-2 ${tone}`}>
        <p className="text-[11px] uppercase font-semibold text-text-secondary">{label}</p>
        <p className="text-sm font-medium text-text-primary break-words">{value || '-'}</p>
    </div>
);

const ActionGroup = ({ label, children }) => (
    <div>
        <p className="text-xs font-semibold text-text-secondary uppercase mb-2">{label}</p>
        <div className="flex flex-col gap-2">{children}</div>
    </div>
);

const ConversationDetailModal = ({ conversationId, isOpen, onClose, onChanged }) => {
    const [conversation, setConversation] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [matchOpen, setMatchOpen] = useState(false);
    const [actionLoading, setActionLoading] = useState('');
    const [notice, setNotice] = useState('');

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
        setNotice('');
        try {
            const response = await fn();
            await load();
            onChanged?.();
            return response;
        } catch (error) {
            alert(error.response?.data?.detail || error.response?.data?.non_field_errors?.[0] || error.message || 'Action failed.');
            return null;
        } finally {
            setActionLoading('');
        }
    };

    const syncChat = async () => {
        const response = await runAction('sync', () => doubletickAPI.syncConversationChat(conversation.id));
        if (!response) return;
        const data = response?.data || {};
        const message = data.warning
            || `Chat synchronized: ${data.created_messages || 0} new messages, ${data.updated_messages || 0} updated.`;
        setNotice(message);
    };

    const sendReply = async (data) => {
        await runAction('reply', () => doubletickAPI.sendConversationReply(conversation.id, data));
    };

    const applySuggestion = () => {
        const suggestion = conversation?.suggested_match;
        if (!suggestion) return;
        const aliasText = conversation.latest_customer_message || '';
        if (suggestion.type === 'area') {
            return runAction('suggestion', () => doubletickAPI.manualCorrect(conversation.id, {
                action: 'correct_area',
                area_id: suggestion.id,
                alias_text: aliasText,
                save_alias: true,
            }));
        }
        if (suggestion.type === 'lead_area') {
            return runAction('suggestion', () => doubletickAPI.matchArea(conversation.id, {
                lead_area_id: suggestion.id,
                raw_alias: aliasText,
                save_alias: true,
                qualify_as_lead: false,
            }));
        }
        if (suggestion.type === 'branch') {
            return runAction('suggestion', () => doubletickAPI.manualCorrect(conversation.id, {
                action: 'correct_branch',
                branch_id: suggestion.id,
            }));
        }
        if (suggestion.type === 'city') {
            return runAction('suggestion', () => doubletickAPI.manualCorrect(conversation.id, {
                action: 'correct_city',
                city_name: suggestion.name,
            }));
        }
        if (suggestion.type === 'location_group') {
            return runAction('suggestion', () => doubletickAPI.manualCorrect(conversation.id, {
                action: 'correct_group',
                group_name: suggestion.name,
            }));
        }
        return null;
    };

    return (
        <>
            <Modal isOpen={isOpen} onClose={onClose} title="WhatsApp Conversation">
                {loading || !conversation ? (
                    <div className="py-16 text-center text-text-secondary">Loading conversation...</div>
                ) : (
                    <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
                        <div className="space-y-4">
                            <div className="rounded-lg border border-border bg-background p-4 space-y-3">
                                <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div className="min-w-0 flex-1">
                                        <h2 className="text-lg font-semibold text-text-primary truncate">{customerName(conversation)}</h2>
                                        <p className="text-sm text-text-secondary truncate">{customerPhone(conversation)}</p>
                                    </div>
                                    <DoubleTickStatusBadge status={conversation.status} />
                                </div>
                                <p className="text-sm text-text-primary break-words line-clamp-2">{conversation.latest_customer_message || conversation.initial_message || 'No customer message on record'}</p>
                                <div className="flex flex-wrap gap-2 pt-2">
                                    <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-primary/10 text-primary">{leadLocation(conversation)}</span>
                                    <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-info/10 text-info">{wabaNumber(conversation)}</span>
                                    {conversation.requires_manual_attention && (
                                        <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-warning/10 text-warning">Manual attention</span>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                                <DetailPill label="Matched Area" value={leadArea(conversation)} />
                                <DetailPill label="Service" value={conversation.raw_service || '-'} />
                                <DetailPill label="Unread" value={conversation.unread_count || 0} />
                                <DetailPill label="Reason" value={pendingReason(conversation)} />
                            </div>

                            {notice && (
                                <div className="flex items-start gap-3 rounded-lg border border-border bg-info/10 px-4 py-3 text-sm text-text-primary">
                                    <CheckCircle2 size={18} className="text-info mt-0.5 flex-shrink-0" />
                                    <p>{notice}</p>
                                </div>
                            )}

                            {conversation.suggested_match && (
                                <div className="rounded-lg border border-warning/30 bg-warning/10 p-4">
                                    <p className="text-xs font-semibold uppercase text-warning">Suggested location</p>
                                    <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
                                        <div>
                                            <p className="font-semibold text-text-primary">{conversation.suggested_match.name}</p>
                                            <p className="text-xs text-text-secondary">
                                                {Math.round((conversation.suggested_match.confidence || 0) * 100)}% confidence · {conversation.suggested_match.reason}
                                            </p>
                                        </div>
                                        <Button loading={actionLoading === 'suggestion'} onClick={applySuggestion}>
                                            <CheckCircle2 size={16} />
                                            Apply suggestion
                                        </Button>
                                    </div>
                                </div>
                            )}

                            <ChatWindow messages={messages} loading={loading} />

                            <ReplyPanel
                                onReply={sendReply}
                                onRequestLocation={() => runAction('location', () => doubletickAPI.requestLocation(conversation.id))}
                                disabled={Boolean(actionLoading)}
                            />
                        </div>

                        <aside className="space-y-4 xl:sticky xl:top-4 self-start">
                            <div className="bg-background border border-border rounded-lg p-4 space-y-3">
                                <h3 className="font-semibold text-text-primary">Conversation Info</h3>
                                <div className="space-y-2 text-sm">
                                    <div>
                                        <p className="text-text-secondary">Area</p>
                                        <p className="font-medium text-text-primary">{leadArea(conversation) || 'Unmatched'}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary">City</p>
                                        <p className="font-medium text-text-primary">{conversation.raw_city || '-'}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary">Service</p>
                                        <p className="font-medium text-text-primary">{conversation.raw_service || 'Unknown'}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary">Status</p>
                                        <p className="font-medium text-text-primary">{conversation.status}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary">Support Owner</p>
                                        <p className="font-medium text-text-primary">{conversation.assigned_support_user || 'Unassigned'}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <ActionGroup label="CRM Matching">
                                    <Button variant="secondary" className="gap-2 justify-start w-full" onClick={() => setMatchOpen(true)}>
                                        <MapPin size={16} />
                                        Correct manually / Add alias
                                    </Button>
                                    {conversation.area_confirmed && conversation.matched_area && (
                                        <Button className="gap-2 justify-start w-full" loading={actionLoading === 'send'} onClick={() => runAction('send', () => doubletickAPI.manualCorrect(conversation.id, { action: 'save_and_send' }))}>
                                            <Send size={16} />
                                            Save and Send to Android
                                        </Button>
                                    )}
                                    <Button variant="secondary" className="gap-2 justify-start w-full" onClick={() => runAction('greeting', () => doubletickAPI.manualCorrect(conversation.id, { action: 'mark_greeting' }))}>
                                        Mark as Greeting
                                    </Button>
                                    <Button variant="secondary" className="gap-2 justify-start w-full" onClick={() => runAction('job', () => doubletickAPI.manualCorrect(conversation.id, { action: 'mark_job' }))}>
                                        Mark as Job Inquiry
                                    </Button>
                                    <Button variant="secondary" className="gap-2 justify-start w-full" onClick={() => runAction('not-location', () => doubletickAPI.manualCorrect(conversation.id, { action: 'mark_not_location' }))}>
                                        Mark as Not Location
                                    </Button>
                                </ActionGroup>

                                <ActionGroup label="Qualification">
                                    <Button variant="secondary" className="gap-2 justify-start w-full" loading={actionLoading === 'qualify'} onClick={() => runAction('qualify', () => doubletickAPI.qualifyConversation(conversation.id))}>
                                        <UserPlus size={16} />
                                        Qualify Lead
                                    </Button>
                                </ActionGroup>

                                <ActionGroup label="Chat Management">
                                    <Button variant="secondary" className="gap-2 justify-start w-full" loading={actionLoading === 'sync'} onClick={syncChat}>
                                        <RefreshCw size={16} />
                                        Sync Chat
                                    </Button>
                                </ActionGroup>

                                <ActionGroup label="Closure">
                                    <Button variant="secondary" className="gap-2 justify-start w-full" loading={actionLoading === 'spam'} onClick={() => runAction('spam', () => doubletickAPI.markSpam(conversation.id))}>
                                        <Flag size={16} />
                                        Mark Spam
                                    </Button>
                                    <Button variant="danger" className="gap-2 justify-start w-full" loading={actionLoading === 'close'} onClick={() => runAction('close', () => doubletickAPI.closeConversation(conversation.id))}>
                                        <Archive size={16} />
                                        Close Conversation
                                    </Button>
                                </ActionGroup>

                                {actionLoading && (
                                    <div className="flex items-center gap-2 text-xs text-text-secondary bg-info/10 border border-info/20 rounded-lg p-3">
                                        <Phone size={14} className="animate-pulse" />
                                        Working on {actionLoading}...
                                    </div>
                                )}
                            </div>
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
