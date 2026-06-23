import React, { useEffect, useState } from 'react';
import { CheckCircle2, MapPin } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const AreaMatchModal = ({ isOpen, conversation, onClose, onSubmit }) => {
    const [form, setForm] = useState({ lead_area_id: '', raw_alias: '', save_alias: true, qualify_as_lead: true });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (conversation) {
            setForm({
                lead_area_id: conversation.matched_area || '',
                raw_alias: conversation.raw_area || '',
                save_alias: true,
                qualify_as_lead: true,
            });
        }
    }, [conversation]);

    const submit = async () => {
        setLoading(true);
        try {
            await onSubmit(form);
            onClose();
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Match WhatsApp Conversation to CRM Area">
            <div className="space-y-5">
                <div className="bg-background border border-border rounded-lg p-4 space-y-2">
                    <h3 className="font-semibold text-text-primary flex items-center gap-2">
                        <MapPin size={16} className="text-primary" />
                        Customer Information
                    </h3>
                    <div className="space-y-1 text-sm">
                        <p><span className="text-text-secondary">Raw area input:</span> <span className="font-medium text-text-primary">{conversation?.raw_area || '-'}</span></p>
                        <p><span className="text-text-secondary">Current city:</span> <span className="font-medium text-text-primary">{conversation?.raw_city || '-'}</span></p>
                        <p><span className="text-text-secondary">Current service:</span> <span className="font-medium text-text-primary">{conversation?.raw_service || '-'}</span></p>
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-semibold text-text-primary mb-2">
                            <CheckCircle2 size={16} className="inline mr-1 text-success" />
                            Select the CRM Area
                        </label>
                        <Input 
                            label="Lead Area ID"
                            placeholder="Enter the matched lead area ID"
                            value={form.lead_area_id} 
                            onChange={(event) => setForm({ ...form, lead_area_id: event.target.value })}
                        />
                        <p className="text-xs text-text-secondary mt-1">Choose the official CRM area this customer belongs to.</p>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-text-primary mb-2">Area Alias (Optional)</label>
                        <Input 
                            placeholder="e.g., North Delhi, Sector 5, Marina"
                            value={form.raw_alias} 
                            onChange={(event) => setForm({ ...form, raw_alias: event.target.value })}
                        />
                        <p className="text-xs text-text-secondary mt-1">Save this customer's area name for faster future matching.</p>
                    </div>

                    <div className="space-y-2 border-t border-border pt-4">
                        <label className="flex items-start gap-3 cursor-pointer">
                            <input 
                                type="checkbox" 
                                checked={form.save_alias} 
                                onChange={(event) => setForm({ ...form, save_alias: event.target.checked })}
                                className="mt-1 h-4 w-4"
                            />
                            <span className="text-sm text-text-primary">
                                Save this alias for future auto-matching
                                <p className="text-xs text-text-secondary font-normal">Customers who mention this area will be matched automatically next time.</p>
                            </span>
                        </label>

                        <label className="flex items-start gap-3 cursor-pointer">
                            <input 
                                type="checkbox" 
                                checked={form.qualify_as_lead} 
                                onChange={(event) => setForm({ ...form, qualify_as_lead: event.target.checked })}
                                className="mt-1 h-4 w-4"
                            />
                            <span className="text-sm text-text-primary">
                                Qualify and distribute as a lead immediately
                                <p className="text-xs text-text-secondary font-normal">Send this conversation to mapped branches for this area right away.</p>
                            </span>
                        </label>
                    </div>
                </div>

                <div className="flex justify-end gap-2 border-t border-border pt-4">
                    <Button variant="secondary" onClick={onClose} disabled={loading}>Cancel</Button>
                    <Button loading={loading} disabled={!form.lead_area_id} onClick={submit}>
                        <CheckCircle2 size={16} />
                        Confirm Match & Proceed
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default AreaMatchModal;
