import React, { useEffect, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useWebSocket } from '../../../shared/hooks/useWebSocket';
import { markAsRead } from '../../../store/slices/notificationSlice';
import { Bell, X, UserCheck } from 'lucide-react';

const RealTimeNotifications = () => {
    const notifications = useSelector((state) => state.notifications.notifications);
    const dispatch = useDispatch();
    const visibleToasts = useMemo(
        () => notifications.filter(n => !n.read).slice(0, 3),
        [notifications]
    );

    // Initialize the shared WebSocket connection
    useWebSocket('/ws/crm/dashboard/');

    useEffect(() => {
        // Auto hide after 5 seconds
        const timers = visibleToasts.map(toast =>
            setTimeout(() => {
                dispatch(markAsRead(toast.id));
            }, 5000)
        );

        return () => timers.forEach(clearTimeout);
    }, [visibleToasts, dispatch]);

    const handleDismiss = (id) => {
        dispatch(markAsRead(id));
    };

    if (visibleToasts.length === 0) return null;

    return (
        <div className="fixed top-20 right-6 z-[9999] flex flex-col gap-3 max-w-sm w-full">
            {visibleToasts.map((toast) => (
                <div 
                    key={toast.id}
                    className="bg-bg-secondary border-l-4 border-primary shadow-2xl rounded-lg p-4 animate-slide-in-right transform transition-all duration-300 hover:scale-[1.02]"
                >
                    <div className="flex items-start gap-3">
                        <div className="bg-primary/10 p-2 rounded-full">
                            <UserCheck className="text-primary" size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                                <h4 className="text-sm font-bold text-text-primary truncate">{toast.title}</h4>
                                <button 
                                    onClick={() => handleDismiss(toast.id)}
                                    className="text-text-quaternary hover:text-text-primary transition-colors duration-200"
                                >
                                    <X size={16} />
                                </button>
                            </div>
                            <p className="text-xs text-text-secondary leading-relaxed">
                                {toast.message}
                            </p>
                            <span className="text-[10px] text-text-quaternary mt-2 block font-medium">
                                Just now
                            </span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default RealTimeNotifications;
