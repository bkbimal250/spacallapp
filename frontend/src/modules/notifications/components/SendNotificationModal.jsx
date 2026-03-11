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
        if (isOpen) {
            fetchDevices();
        }
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
        setLoading(true);
        try {
            await onSend({
                device_ids: selectedDevices,
                title,
                body,
                type
            });
            setTitle('');
            setBody('');
            setSelectedDevices([]);
            onClose();
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm" onClick={onClose}></div>
            
            <div className="relative bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="bg-gradient-to-r from-sky-600 to-indigo-600 p-6 text-white relative">
                    <button onClick={onClose} className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-full transition-colors">
                        <X size={20} />
                    </button>
                    <div className="flex items-center space-x-3">
                        <div className="bg-white/20 p-2 rounded-xl backdrop-blur-md">
                            <Send size={24} className="text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-black">Push Notification</h2>
                            <p className="text-sky-100/80 text-xs font-medium uppercase tracking-widest">Send alert to devices</p>
                        </div>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    <div className="grid grid-cols-2 gap-3">
                        {[
                            { id: 'system', icon: Bell, label: 'System', color: 'bg-sky-50 text-sky-600' },
                            { id: 'reminder', icon: Smartphone, label: 'Reminder', color: 'bg-indigo-50 text-indigo-600' },
                            { id: 'alert', icon: AlertTriangle, label: 'Critical', color: 'bg-orange-50 text-orange-600' },
                            { id: 'sync_issue', icon: ShieldAlert, label: 'Sync/Ops', color: 'bg-rose-50 text-rose-600' }
                        ].map(t => (
                            <button
                                key={t.id}
                                type="button"
                                onClick={() => setType(t.id)}
                                className={`flex items-center space-x-2 p-3 rounded-2xl border-2 transition-all ${
                                    type === t.id 
                                    ? 'border-sky-500 bg-sky-50 ring-4 ring-sky-500/10' 
                                    : 'border-gray-50 bg-gray-50/50 grayscale opacity-60 hover:grayscale-0 hover:opacity-100'
                                }`}
                            >
                                <t.icon size={18} className={t.color} />
                                <span className={`text-xs font-bold ${type === t.id ? 'text-sky-900' : 'text-gray-500'}`}>{t.label}</span>
                            </button>
                        ))}
                    </div>

                    <div className="space-y-1">
                        <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Target Devices</label>
                        <select 
                            multiple
                            className="w-full bg-gray-50 border-none rounded-2xl p-3 text-sm focus:ring-4 ring-sky-500/10 transition-all min-h-[100px]"
                            value={selectedDevices}
                            onChange={(e) => setSelectedDevices(Array.from(e.target.selectedOptions, option => option.value))}
                        >
                            <option value="">All Active Devices</option>
                            {devices.map(d => (
                                <option key={d.id} value={d.id}>
                                    {d.device_id} ({d.branch_name})
                                </option>
                            ))}
                        </select>
                        <p className="text-[9px] text-gray-400 mt-1">* Leave empty to send to all active devices</p>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Title</label>
                            <input 
                                type="text"
                                required
                                placeholder="e.g. Sync Successful"
                                className="w-full bg-gray-50 border-none rounded-2xl p-4 text-sm focus:ring-4 ring-sky-500/10 transition-all placeholder:text-gray-300"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Message Body</label>
                            <textarea 
                                required
                                rows={3}
                                placeholder="Write your message here..."
                                className="w-full bg-gray-50 border-none rounded-2xl p-4 text-sm focus:ring-4 ring-sky-500/10 transition-all placeholder:text-gray-300 resize-none"
                                value={body}
                                onChange={(e) => setBody(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="pt-2 flex space-x-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-6 py-4 rounded-2xl text-sm font-bold text-gray-500 hover:bg-gray-100 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-[2] bg-gray-900 text-white rounded-2xl py-4 font-black flex items-center justify-center space-x-2 hover:bg-black transition-all disabled:opacity-50"
                        >
                            {loading ? (
                                <div className="h-4 w-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    <span>Send Notification</span>
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
