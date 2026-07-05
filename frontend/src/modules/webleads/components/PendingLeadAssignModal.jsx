import React, { useEffect, useState } from 'react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { usersAPI } from '../../users/api';
import BranchSearchSelect from './BranchSearchSelect';

const PendingLeadAssignModal = ({ lead, isOpen, onClose, onSubmit, saving = false }) => {
    const [users, setUsers] = useState([]);
    const [payload, setPayload] = useState({ branch: '', assigned_to: '' });

    useEffect(() => {
        if (!isOpen) return;
        usersAPI.getUsers({ page_size: 500 }).then((res) => setUsers(res.data.results || res.data || [])).catch(() => setUsers([]));
        setPayload({ branch: '', assigned_to: '' });
    }, [isOpen]);

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Assign Website Lead" maxWidth="max-w-lg" hideFooter>
            <div className="space-y-4">
                <div className="rounded-lg border border-border bg-background p-3 text-sm text-text-secondary">
                    {lead?.customer_name} from {lead?.website_name}
                </div>
                <div>
                    <label className="block text-sm font-medium text-text-primary">Branch/Spa</label>
                    <BranchSearchSelect
                        className="mt-1"
                        value={payload.branch}
                        onChange={(value) => setPayload((prev) => ({ ...prev, branch: value }))}
                        placeholder="Search branch, area, or city"
                        allowEmpty={false}
                    />
                </div>
                <label className="block text-sm font-medium text-text-primary">Assign To
                    <select className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={payload.assigned_to} onChange={(e) => setPayload((prev) => ({ ...prev, assigned_to: e.target.value }))}>
                        <option value="">No specific user</option>
                        {users.map((user) => <option key={user.id} value={user.id}>{user.full_name || user.email || user.username}</option>)}
                    </select>
                </label>
                <div className="flex justify-end gap-2">
                    <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
                    <Button type="button" loading={saving} disabled={!payload.branch} onClick={() => onSubmit({ branch: payload.branch, assigned_to: payload.assigned_to || null })}>Save</Button>
                </div>
            </div>
        </Modal>
    );
};

export default PendingLeadAssignModal;
