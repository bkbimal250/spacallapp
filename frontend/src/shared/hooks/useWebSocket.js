import { useEffect, useCallback } from 'react';
import { websocketService } from '../services/websocketService';
import { useDispatch, useSelector } from 'react-redux';
import { handleUserLogin, updateUserStatus, addNotification } from '../../store/slices/notificationSlice';

export const useWebSocket = (path) => {
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
        }
    }, [dispatch]);

    useEffect(() => {
        if (user && path) {
            websocketService.connect(path);
            const unsubscribe = websocketService.subscribe(onMessage);
            return () => {
                unsubscribe();
                // websocketService.disconnect();
            };
        }
    }, [user, path, onMessage]);

    return {
        send: websocketService.send.bind(websocketService)
    };
};
