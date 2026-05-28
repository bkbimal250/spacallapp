import React, { useState, useEffect } from 'react';
import { X, Send, Smartphone, Bell, AlertTriangle, ShieldAlert, UserRound, Search } from 'lucide-react';
import { devicesAPI } from '../../devices/api';
import { usersAPI } from '../../users/api';

const SendNotificationModal = ({ isOpen, onClose, onSend }) => {
    const [devices, setDevices] = useState([]);
    const [users, setUsers] = useState([]);
    const [targetType, setTargetType] = useState('devices');
    const [selectedDevices, setSelectedDevices] = useState([]);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [targetSearch, setTargetSearch] = useState('');
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [type, setType] = useState('system');
    const [loading, setLoading] = useState(false);
    const [fetchingDevices, setFetchingDevices] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchDevices();
            fetchUsers();
        }
    }, [isOpen]);

    const fetchDevices = async () => {
        setFetchingDevices(true);
        try {
            const res = await devicesAPI.getDevices({ is_active: true, page_size: 400 });
            setDevices(res.data.results || res.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setFetchingDevices(false);
        }
    };

    const fetchUsers = async () => {
        try {
            const res = await usersAPI.getUsers({ is_active: true, page_size: 400 });
            setUsers(res.data.results || res.data || []);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const deviceIds = selectedDevices.filter(id => id !== '');
        const userIds = selectedUsers.filter(id => id !== '');
        
        setLoading(true);
        try {
            await onSend({
                target_type: targetType,
                device_ids: deviceIds,
                user_ids: userIds,
                title,
                body,
                type
            });
            setTitle('');
            setBody('');
            setSelectedDevices([]);
            setSelectedUsers([]);
            onClose();
        } catch (err) {
            console.error('Failed to send notification:', err);
            // Error handling is managed by the parent's try-catch but we could show a toast here if available
        } finally {
            setLoading(false);
        }
    };

    const getDeviceLabel = (device) => {
        const phone = device.sim_1_number || device.sim_2_number || 'No SIM';
        return `${device.phone_name || device.device_id} - ${phone} (${device.branch_name})`;
    };

    const getUserLabel = (user) => (
        `${user.full_name || user.email} - ${user.phone_number || 'No phone'} (${user.role?.replace('_', ' ')})`
    );

    const filteredDevices = devices.filter((device) =>
        getDeviceLabel(device).toLowerCase().includes(targetSearch.toLowerCase())
    );

    const filteredUsers = users.filter((user) =>
        getUserLabel(user).toLowerCase().includes(targetSearch.toLowerCase())
    );

    const toggleSelection = (id, selectedValues, setSelectedValues) => {
        setSelectedValues((prev) => {
            const current = prev.length === 0 ? [] : selectedValues;
            return current.includes(id)
                ? current.filter(value => value !== id)
                : [...current, id];
        });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">

            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            <div className="relative bg-card border border-border rounded-xl shadow-xl w-full max-w-lg overflow-hidden text-text-primary">

                <div className="flex items-center justify-between px-6 py-4 border-b border-border">

                    <div className="flex items-center gap-3">
                        <div className="bg-primary/20 p-2 rounded-lg">
                            <Send size={20} className="text-primary" />
                        </div>

                        <div>
                            <h2 className="text-lg font-semibold">
                                Push Notification
                            </h2>
                            <p className="text-xs text-text-secondary">
                                Send alert to devices
                            </p>
                        </div>
                    </div>

                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-cardHover rounded"
                    >
                        <X size={18} />
                    </button>

                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-5">

                    <div className="grid grid-cols-2 gap-3">

                        {[
                            { id: 'system', icon: Bell, label: 'System' },
                            { id: 'reminder', icon: Smartphone, label: 'Reminder' },
                            { id: 'alert', icon: AlertTriangle, label: 'Critical' },
                            { id: 'sync_issue', icon: ShieldAlert, label: 'Sync/Ops' }
                        ].map(t => (
                            <button
                                key={t.id}
                                type="button"
                                onClick={() => setType(t.id)}
                                className={`flex items-center gap-2 p-3 rounded-lg border transition ${type === t.id
                                        ? 'border-primary bg-primary/10 text-primary'
                                        : 'border-border bg-background text-text-secondary hover:bg-cardHover'
                                    }`}
                            >
                                <t.icon size={16} />
                                <span className="text-xs font-medium">{t.label}</span>
                            </button>
                        ))}

                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        {[
                            { id: 'devices', icon: Smartphone, label: 'Device Phones' },
                            { id: 'users', icon: UserRound, label: 'User Phones' }
                        ].map(target => (
                            <button
                                key={target.id}
                                type="button"
                                onClick={() => {
                                    setTargetType(target.id);
                                    setSelectedDevices([]);
                                    setSelectedUsers([]);
                                    setTargetSearch('');
                                }}
                                className={`flex items-center justify-center gap-2 p-3 rounded-lg border transition ${targetType === target.id
                                        ? 'border-primary bg-primary/10 text-primary'
                                        : 'border-border bg-background text-text-secondary hover:bg-cardHover'
                                    }`}
                            >
                                <target.icon size={16} />
                                <span className="text-xs font-medium">{target.label}</span>
                            </button>
                        ))}
                    </div>

                    <div className="space-y-1">

                        <label className="text-xs text-text-secondary">
                            {targetType === 'devices' ? 'Target Device Phones' : 'Target User Phones'}
                        </label>

                        <div className="relative">
                            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                            <input
                                type="search"
                                value={targetSearch}
                                onChange={(e) => setTargetSearch(e.target.value)}
                                placeholder={targetType === 'devices' ? 'Search device, phone, or branch...' : 'Search user, phone, email, or role...'}
                                className="w-full bg-background border border-border rounded-lg py-2.5 pl-9 pr-3 text-sm outline-none focus:border-primary"
                            />
                        </div>

                        <div className="border border-border rounded-lg bg-background overflow-hidden">
                            <label className="flex items-center gap-3 px-3 py-2.5 border-b border-border cursor-pointer hover:bg-cardHover">
                                <input
                                    type="checkbox"
                                    checked={targetType === 'devices' ? selectedDevices.length === 0 : selectedUsers.length === 0}
                                    onChange={() => {
                                        setSelectedDevices([]);
                                        setSelectedUsers([]);
                                    }}
                                    className="h-4 w-4 accent-primary"
                                />
                                <span className="text-sm font-medium text-text-primary">
                                    {targetType === 'devices' ? 'All Active Device Phones' : 'All Users With App Tokens'}
                                </span>
                            </label>

                            <div className="max-h-44 overflow-y-auto divide-y divide-border">
                                {targetType === 'devices' ? (
                                    filteredDevices.length > 0 ? filteredDevices.map(device => (
                                        <label
                                            key={device.id}
                                            className="flex items-start gap-3 px-3 py-2.5 cursor-pointer hover:bg-cardHover"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedDevices.includes(device.id)}
                                                onChange={() => toggleSelection(device.id, selectedDevices, setSelectedDevices)}
                                                className="mt-0.5 h-4 w-4 accent-primary"
                                            />
                                            <span className="text-sm text-text-secondary">
                                                {getDeviceLabel(device)}
                                            </span>
                                        </label>
                                    )) : (
                                        <div className="px-3 py-6 text-center text-sm text-text-muted">
                                            No device phones found.
                                        </div>
                                    )
                                ) : (
                                    filteredUsers.length > 0 ? filteredUsers.map(user => (
                                        <label
                                            key={user.id}
                                            className="flex items-start gap-3 px-3 py-2.5 cursor-pointer hover:bg-cardHover"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedUsers.includes(user.id)}
                                                onChange={() => toggleSelection(user.id, selectedUsers, setSelectedUsers)}
                                                className="mt-0.5 h-4 w-4 accent-primary"
                                            />
                                            <span className="text-sm text-text-secondary">
                                                {getUserLabel(user)}
                                            </span>
                                        </label>
                                    )) : (
                                        <div className="px-3 py-6 text-center text-sm text-text-muted">
                                            No user phones found.
                                        </div>
                                    )
                                )}
                            </div>
                        </div>

                        <p className="text-xs text-text-secondary">
                            {(targetType === 'devices' ? selectedDevices.length : selectedUsers.length) === 0
                                ? 'All matching phones will receive this notification.'
                                : `${targetType === 'devices' ? selectedDevices.length : selectedUsers.length} phone(s) selected.`}
                            {fetchingDevices ? ' Loading phones...' : ''}
                        </p>

                    </div>

                    <div className="space-y-4">

                        <div className="space-y-1">
                            <label className="text-xs text-text-secondary">
                                Title
                            </label>

                            <input
                                type="text"
                                required
                                placeholder="e.g. Sync Successful"
                                className="w-full bg-background border border-border rounded-lg p-3 text-sm"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                            />
                        </div>

                        <div className="space-y-1">

                            <label className="text-xs text-text-secondary">
                                Message
                            </label>

                            <textarea
                                required
                                rows={3}
                                placeholder="Write your message..."
                                className="w-full bg-background border border-border rounded-lg p-3 text-sm resize-none"
                                value={body}
                                onChange={(e) => setBody(e.target.value)}
                            />

                        </div>

                    </div>

                    <div className="flex gap-3 pt-2">

                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-3 rounded-lg border border-border text-text-secondary hover:bg-cardHover"
                        >
                            Cancel
                        </button>

                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-[2] bg-primary text-white rounded-lg py-3 flex items-center justify-center gap-2 hover:bg-primary-hover disabled:opacity-50"
                        >

                            {loading ? (
                                <div className="h-4 w-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    Send Notification
                                    <Send size={16} />
                                </>
                            )}

                        </button>

                    </div>

                </form>

            </div>

        </div>
    );
};

export default SendNotificationModal;
