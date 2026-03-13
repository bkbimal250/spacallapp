import React, { useState, useEffect } from 'react';
import { X, Send, Smartphone, Bell, AlertTriangle, ShieldAlert } from 'lucide-react';
import { devicesAPI } from '../../devices/api';

const SendNotificationModal = ({ isOpen, onClose, onSend }) => {
    const [devices, setDevices] = useState([]);
    const [selectedDevices, setSelectedDevices] = useState([]);
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [type, setType] = useState('system');
    const [loading, setLoading] = useState(false);
    const [fetchingDevices, setFetchingDevices] = useState(false);

    useEffect(() => {
        if (isOpen) fetchDevices();
    }, [isOpen]);

    const fetchDevices = async () => {
        setFetchingDevices(true);
        try {
            const res = await devicesAPI.getAll({ is_active: true });
            setDevices(res.data.results || res.data || []);
        } catch (err) {
            console.error(err);
        } finally {
            setFetchingDevices(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Filter out empty strings which represent "All" but shouldn't be sent as individual IDs
        const deviceIds = selectedDevices.filter(id => id !== '');
        
        setLoading(true);
        try {
            await onSend({
                device_ids: deviceIds,
                title,
                body,
                type
            });
            setTitle('');
            setBody('');
            setSelectedDevices([]);
            onClose();
        } catch (err) {
            console.error('Failed to send notification:', err);
            // Error handling is managed by the parent's try-catch but we could show a toast here if available
        } finally {
            setLoading(false);
        }
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

                    <div className="space-y-1">

                        <label className="text-xs text-text-secondary">
                            Target Devices
                        </label>

                        <select
                            multiple
                            className="w-full bg-background border border-border rounded-lg p-3 text-sm min-h-[100px]"
                            value={selectedDevices}
                            onChange={(e) =>
                                setSelectedDevices(
                                    Array.from(e.target.selectedOptions, option => option.value)
                                )
                            }
                        >

                            <option value="">All Active Devices</option>

                            {devices.map(d => (
                                <option key={d.id} value={d.id}>
                                    {d.device_id} ({d.branch_name})
                                </option>
                            ))}

                        </select>

                        <p className="text-xs text-text-secondary">
                            Leave empty to send to all devices
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