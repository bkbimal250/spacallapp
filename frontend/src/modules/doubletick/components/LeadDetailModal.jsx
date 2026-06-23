import React, { useEffect, useState } from 'react';
import { Activity, Archive, MapPin, MessageSquareText, RefreshCw, Send } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { doubletickAPI } from '../api';
import ChatWindow from './ChatWindow';
import ReplyPanel from './ReplyPanel';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import MatchConfidenceBadge from './MatchConfidenceBadge';
import AndroidVisibilityPanel from './AndroidVisibilityPanel';
import LeadLocationCorrectionModal from './LeadLocationCorrectionModal';
import { formatDate } from '../../../shared/utils/formatDate';
import { customerName, customerPhone, leadArea, leadBranch, leadOwner, wabaNumber } from '../display';

const Info = ({ label, value }) => (
    <div className="border-b border-border/60 py-2 last:border-0">
        <p className="text-[11px] font-semibold uppercase text-text-secondary">{label}</p>
        <p className="break-words text-sm font-medium text-text-primary">{value || '-'}</p>
    </div>
);

const LeadDetailModal = ({ leadId, isOpen, onClose, onChanged }) => {
    const [lead, setLead] = useState(null);
    const [messages, setMessages] = useState([]);
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState('');
    const [correctionOpen, setCorrectionOpen] = useState(false);

    const load = async () => {
        if (!leadId) return;
        setLoading(true);
        try {
            const [detail, chat, timeline] = await Promise.all([
                doubletickAPI.getLead(leadId),
                doubletickAPI.getLeadMessages(leadId),
                doubletickAPI.getLeadActivities(leadId),
            ]);
            setLead(detail.data);
            setMessages(chat.data.results || chat.data || []);
            setActivities(timeline.data.results || timeline.data || []);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { if (isOpen) load(); }, [isOpen, leadId]); // eslint-disable-line react-hooks/exhaustive-deps

    const run = async (name, action) => {
        setActionLoading(name);
        try {
            await action();
            await load();
            onChanged?.();
        } catch (error) {
            alert(error.response?.data?.detail || error.message || 'Action failed.');
        } finally {
            setActionLoading('');
        }
    };

    return (
        <>
            <Modal isOpen={isOpen} onClose={onClose} title="DoubleTick Lead Workspace" maxWidth="max-w-[1500px]" hideFooter>
                {loading || !lead ? (
                    <div className="py-20 text-center text-text-secondary">Loading lead workspace...</div>
                ) : (
                    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[300px_minmax(480px,1fr)_340px]">
                        <aside className="space-y-4">
                            <div className="rounded-lg border border-border bg-background p-4">
                                <div className="mb-3 flex items-start justify-between gap-2">
                                    <div className="min-w-0">
                                        <h2 className="truncate font-semibold text-text-primary">{customerName(lead)}</h2>
                                        <p className="text-sm text-text-secondary">{customerPhone(lead)}</p>
                                    </div>
                                    <DoubleTickStatusBadge status={lead.status} type="lead" />
                                </div>
                                <Info label="Channel / WABA" value={wabaNumber(lead)} />
                                <Info label="Classification" value={lead.classification} />
                                <Info label="Match Method" value={lead.match_method === 'fuzzy' ? 'RapidFuzz' : lead.match_method} />
                                <div className="py-2"><MatchConfidenceBadge confidence={lead.match_confidence} /></div>
                                <Info label="Raw City" value={lead.raw_city} />
                                <Info label="Raw Group" value={lead.raw_group} />
                                <Info label="Raw Area" value={lead.raw_area} />
                                <Info label="Matched Area" value={leadArea(lead)} />
                                <Info label="Branch / Spa" value={leadBranch(lead)} />
                                <Info label="Owner" value={leadOwner(lead)} />
                                <Info label="Device" value={lead.current_device_name || lead.assigned_device_name} />
                            </div>
                            {lead.suggested_match && (
                                <div className="rounded-lg border border-warning/30 bg-warning/10 p-4">
                                    <p className="text-xs font-semibold uppercase text-warning">RapidFuzz suggestion</p>
                                    <p className="mt-1 font-semibold text-text-primary">{lead.suggested_match.name}</p>
                                    <p className="text-xs text-text-secondary">{lead.suggested_match.reason}</p>
                                    <Button className="mt-3 w-full justify-center" onClick={() => setCorrectionOpen(true)}>
                                        <MapPin size={15} /> Review & Apply
                                    </Button>
                                </div>
                            )}
                        </aside>

                        <main className="min-w-0 space-y-3">
                            <div className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3">
                                <div>
                                    <p className="font-semibold text-text-primary">WhatsApp Timeline</p>
                                    <p className="text-xs text-text-secondary">{messages.length} synchronized messages</p>
                                </div>
                                <Button variant="secondary" loading={actionLoading === 'refresh'} onClick={() => run('refresh', load)}>
                                    <RefreshCw size={15} /> Refresh
                                </Button>
                            </div>
                            <ChatWindow messages={messages} loading={loading} />
                        </main>

                        <aside className="space-y-4 xl:sticky xl:top-0 xl:self-start">
                            <ReplyPanel disabled={Boolean(actionLoading)}
                                onReply={(data) => run('reply', () => doubletickAPI.replyLead(lead.id, data))}
                                onRequestLocation={() => run('location', () => doubletickAPI.requestLocation(lead.conversation))}
                                lastLocationRequestAt={[...messages].reverse().find((item) =>
                                    item.direction === 'outbound'
                                    && String(item.text || '').includes('Provide Me Your Location')
                                )?.timestamp} />

                            <div className="rounded-lg border border-border bg-background p-4 space-y-2">
                                <p className="font-semibold text-text-primary">Location Actions</p>
                                <Button variant="secondary" className="w-full justify-start" onClick={() => setCorrectionOpen(true)}>
                                    <MapPin size={16} /> Manual Correction / Alias
                                </Button>
                                <Button variant="secondary" className="w-full justify-start" disabled={!lead.conversation}
                                    loading={actionLoading === 'location'} onClick={() => run('location', () => doubletickAPI.requestLocation(lead.conversation))}>
                                    <Send size={16} /> Send Location Request
                                </Button>
                            </div>

                            <AndroidVisibilityPanel lead={lead} loading={actionLoading === 'android'}
                                onSend={() => run('android', () => doubletickAPI.distributeLead(lead.id))} />

                            <div className="rounded-lg border border-border bg-background p-4">
                                <p className="mb-3 flex items-center gap-2 font-semibold text-text-primary"><Activity size={16} /> Activity Log</p>
                                <div className="max-h-64 space-y-3 overflow-y-auto">
                                    {activities.length === 0 ? <p className="text-sm text-text-secondary">No activity yet.</p> : activities.map((item) => (
                                        <div key={item.id} className="border-l-2 border-primary/30 pl-3">
                                            <p className="text-sm font-medium text-text-primary">{String(item.action || '').replaceAll('_', ' ')}</p>
                                            {item.note && <p className="text-xs text-text-secondary">{item.note}</p>}
                                            <p className="text-[11px] text-text-secondary">{item.created_at ? formatDate(item.created_at, 'MMM dd, HH:mm') : '-'}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <Button variant="danger" className="w-full justify-center" loading={actionLoading === 'close'}
                                onClick={() => run('close', () => doubletickAPI.closeLead(lead.id, { reason: 'Closed from CRM lead workspace.' }))}>
                                <Archive size={16} /> Close Lead
                            </Button>
                        </aside>
                    </div>
                )}
            </Modal>
            <LeadLocationCorrectionModal isOpen={correctionOpen} lead={lead}
                onClose={() => setCorrectionOpen(false)} onSaved={async () => { await load(); onChanged?.(); }} />
        </>
    );
};

export default LeadDetailModal;
