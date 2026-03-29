import { CONFIG } from '../../app/config';
import { getToken } from './tokenService';

class WebSocketService {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = new Set();
    }

    connect(path) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;
        }

        const token = getToken();
        // Django Channels AuthMiddlewareStack often expects token in headers or query param
        // For standard WebSocket API, we usually pass it in a custom query param if not using subprotocols
        const wsUrl = `${CONFIG.WS_BASE_URL}${path}?token=${token}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket Connected');
            this.reconnectAttempts = 0;
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.listeners.forEach(listener => listener(data));
        };

        this.socket.onclose = () => {
            console.log('WebSocket Disconnected');
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    this.connect(path);
                }, 3000 * this.reconnectAttempts);
            }
        };

        this.socket.onerror = (err) => {
            console.error('WebSocket Error:', err);
        };
    }

    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

export const websocketService = new WebSocketService();
