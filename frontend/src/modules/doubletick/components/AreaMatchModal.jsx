import React, { useEffect, useState } from 'react';
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
        <Modal isOpen={isOpen} onClose={onClose} title="Match CRM Area">
            <div className="space-y-4">
                <Input label="Lead Area ID" value={form.lead_area_id} onChange={(event) => setForm({ ...form, lead_area_id: event.target.value })} />
                <Input label="Raw customer area / alias" value={form.raw_alias} onChange={(event) => setForm({ ...form, raw_alias: event.target.value })} />
                <label className="flex items-center gap-2 text-sm text-text-primary">
                    <input type="checkbox" checked={form.save_alias} onChange={(event) => setForm({ ...form, save_alias: event.target.checked })} />
                    Save this alias for future auto matching
                </label>
                <label className="flex items-center gap-2 text-sm text-text-primary">
                    <input type="checkbox" checked={form.qualify_as_lead} onChange={(event) => setForm({ ...form, qualify_as_lead: event.target.checked })} />
                    Qualify and distribute after matching
                </label>
                <div className="flex justify-end">
                    <Button loading={loading} disabled={!form.lead_area_id} onClick={submit}>Save Match</Button>
                </div>
            </div>
        </Modal>
    );
};

export default AreaMatchModal;
