import React, { useEffect, useState } from 'react';
import { Archive, CheckCircle2, PhoneCall, RefreshCw, RotateCcw, Send, UserCheck } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { doubletickAPI } from '../api';
import ChatWindow from './ChatWindow';
import DoubleTickStatusBadge from './DoubleTickStatusBadge';
import { formatDate } from '../../../shared/utils/formatDate';

const LeadDetailModal = ({ leadId, isOpen, onClose, onChanged }) => {
    const [lead, setLead] = useState(null);
    const [messages, setMessages] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState('');
    const [note, setNote] = useState('');

    const load = async () => {
        if (!leadId) return;
        setLoading(true);
        try {
            const [detail, chat, attempts] = await Promise.all([
                doubletickAPI.getLead(leadId),
                doubletickAPI.getLeadMessages(leadId),
                doubletickAPI.getLeadAssignments(leadId),
            ]);
            setLead(detail.data);
            setMessages(chat.data.results || chat.data || []);
            setAssignments(attempts.data.results || attempts.data || []);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen, leadId]);

    const run = async (name, fn) => {
        setActionLoading(name);
        try {
            await fn();
            setNote('');
            await load();
            onChanged?.();
        } catch (error) {
            alert(error.response?.data?.detail || error.message || 'Action failed.');
        } finally {
            setActionLoading('');
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="DoubleTick Lead">
            {loading || !lead ? (
                <div className="py-16 text-center text-text-secondary">Loading lead...</div>
            ) : (
                <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-5">
                    <div className="space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h2 className="text-lg font-semibold">{lead.customer_name || lead.phone_number || 'Lead'}</h2>
                                <p className="text-sm text-text-secondary">{lead.phone_number} · {lead.matched_area_name || lead.raw_area || '-'}</p>
                            </div>
                            <DoubleTickStatusBadge status={lead.status} type="lead" />
                        </div>
                        <ChatWindow messages={messages} />
                        <div className="bg-background border border-border rounded-lg p-4">
                            <h3 className="font-semibold mb-3">Assignment Attempts</h3>
                            <div className="space-y-2">
                                {assignments.length === 0 ? (
                                    <p className="text-sm text-text-secondary">No claim attempts yet.</p>
                                ) : assignments.map((assignment) => (
                                    <div key={assignment.id} className="border border-border rounded-lg p-3 text-sm">
                                        <p className="font-medium">Attempt {assignment.attempt_number} · {assignment.status}</p>
                                        <p className="text-text-secondary">{assignment.assigned_user_name || 'Unknown'} · {assignment.branch_name || '-'}</p>
                                        <p className="text-xs text-text-secondary">{assignment.claimed_at ? formatDate(assignment.claimed_at, 'MMM dd, HH:mm') : '-'}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    <aside className="space-y-4">
                        <div className="bg-background border border-border rounded-lg p-4 space-y-2 text-sm">
                            <p><span className="text-text-secondary">Current owner:</span> {lead.current_user_name || 'Unclaimed'}</p>
                            <p><span className="text-text-secondary">Current branch:</span> {lead.current_branch_name || '-'}</p>
                            <p><span className="text-text-secondary">Service:</span> {lead.raw_service || lead.service_name || '-'}</p>
                            <p><span className="text-text-secondary">Created:</span> {lead.created_at ? formatDate(lead.created_at, 'MMM dd, HH:mm') : '-'}</p>
                        </div>
                        <textarea
                            className="w-full min-h-[88px] bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary resize-none"
                            placeholder="Action note"
                            value={note}
                            onChange={(event) => setNote(event.target.value)}
                        />
                        <div className="grid grid-cols-1 gap-2">
                            <Button className="gap-2 justify-start" loading={actionLoading === 'claim'} onClick={() => run('claim', () => doubletickAPI.claimLead(lead.id))}>
                                <UserCheck size={16} />
                                Claim
                            </Button>
                            <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'start'} onClick={() => run('start', () => doubletickAPI.startContact(lead.id, { note }))}>
                                <PhoneCall size={16} />
                                Start Contact
                            </Button>
                            <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'contacted'} onClick={() => run('contacted', () => doubletickAPI.updateLeadStatus(lead.id, { action: 'contacted', note }))}>
                                <CheckCircle2 size={16} />
                                Mark Contacted
                            </Button>
                            <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'follow'} onClick={() => run('follow', () => doubletickAPI.followUpLead(lead.id, { note }))}>
                                <RefreshCw size={16} />
                                Follow Up
                            </Button>
                            <Button variant="secondary" className="gap-2 justify-start" loading={actionLoading === 'booked'} onClick={() => run('booked', () => doubletickAPI.updateLeadStatus(lead.id, { action: 'booked', note }))}>
                                <Send size={16} />
                                Booked
                            </Button>
                            <Button variant="outline" className="gap-2 justify-start" loading={actionLoading === 'release'} onClick={() => run('release', () => doubletickAPI.releaseMobileLead(lead.id, { reason: note }))}>
                                <RotateCcw size={16} />
                                Release
                            </Button>
                            <Button variant="danger" className="gap-2 justify-start" loading={actionLoading === 'close'} onClick={() => run('close', () => doubletickAPI.closeLead(lead.id, { reason: note }))}>
                                <Archive size={16} />
                                Close
                            </Button>
                        </div>
                    </aside>
                </div>
            )}
        </Modal>
    );
};

export default LeadDetailModal;
