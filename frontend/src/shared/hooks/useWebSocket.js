import { useEffect, useCallback } from 'react';
import { websocketService } from '../services/websocketService';
import { useDispatch, useSelector } from 'react-redux';
import { handleUserLogin, updateUserStatus, addNotification } from '../../store/slices/notificationSlice';

export const useWebSocket = (path, customOnMessage) => {
    const dispatch = useDispatch();
    const { user } = useSelector((state) => state.auth);

    const onMessage = useCallback((data) => {
        if (data.type === 'user_login') {
            dispatch(handleUserLogin(data));
            dispatch(addNotification({
                title: 'User Login',
                message: `${data.name} (${data.role}) from ${data.branch} just logged in.`,
                type: 'info'
            }));
        } else if (data.type === 'user_status_change') {
            dispatch(updateUserStatus(data));
        } else if (data.type === 'notification_created') {
            // Add to global notifications for toasts
            dispatch(addNotification({
                id: data.notification.id,
                title: data.notification.title,
                message: data.notification.body,
                type: data.notification.notification_type || 'info',
                created_at: data.notification.created_at
            }));
        }

        // Call custom callback if provided
        if (customOnMessage) {
            customOnMessage(data);
        }
    }, [dispatch, customOnMessage]);

    useEffect(() => {
        if (user && path) {
            websocketService.connect(path);
            const unsubscribe = websocketService.subscribe(onMessage);
            return () => {
                unsubscribe();
            };
        }
    }, [user, path, onMessage]);

    return {
        send: websocketService.send.bind(websocketService)
    };
};
