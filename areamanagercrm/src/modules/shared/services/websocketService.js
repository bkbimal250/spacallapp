import { CONFIG } from '../../app/config';
import { getToken } from './tokenService';

class WebSocketService {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = new Set();
        this.currentPath = null;
        this.manualClose = false;
        this.isConnecting = false;
    }

    /**
     * Connect to WebSocket with token authentication
     */
    connect(path) {
        // Prevent duplicate connections
        if (
            this.socket &&
            (this.socket.readyState === WebSocket.OPEN ||
                this.socket.readyState === WebSocket.CONNECTING)
        ) {
            return;
        }

        this.currentPath = path;
        this.manualClose = false;

        const token = getToken();
        if (!token) {
            console.warn('⚠️ No token found. Skipping WebSocket connection.');
            return;
        }

        const wsUrl = `${CONFIG.WS_BASE_URL}${path}?token=${token}`;
        console.log(`🔌 Connecting WebSocket: ${wsUrl.replace(token, 'REDACTED')}`);

        try {
            this.isConnecting = true;
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log('✅ WebSocket Connected');
                this.reconnectAttempts = 0;
                this.isConnecting = false;
            };

            this.socket.onmessage = (event) => {
                const rawData = event.data;
                // Move parsing and execution to next tick to avoid blocking the main thread
                // This resolves the [Violation] 'message' handler warnings
                setTimeout(() => {
                    try {
                        const data = JSON.parse(rawData);
                        this.listeners.forEach(listener => {
                            try {
                                listener(data);
                            } catch (e) {
                                console.error('❌ Error in WebSocket listener:', e);
                            }
                        });
                    } catch (error) {
                        console.error('❌ WebSocket JSON parse error:', error);
                    }
                }, 0);
            };

            this.socket.onclose = (event) => {
                console.log(`❌ WebSocket Closed (Code: ${event.code})`);

                this.socket = null;
                this.isConnecting = false;

                // Reconnect logic
                if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.min(10000, 3000 * (this.reconnectAttempts + 1));

                    console.log(`🔄 Reconnecting in ${delay}ms...`);

                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connect(this.currentPath);
                    }, delay);
                }
            };

            this.socket.onerror = (error) => {
                console.error('🚨 WebSocket Error:', error);
            };

        } catch (error) {
            console.error('🚨 WebSocket init error:', error);
            this.isConnecting = false;
        }
    }

    /**
     * Subscribe to WebSocket messages
     */
    subscribe(listener) {
        this.listeners.add(listener);

        // Ensure connection exists
        if (!this.socket && !this.isConnecting && this.currentPath) {
            this.connect(this.currentPath);
        }

        return () => {
            this.listeners.delete(listener);
            // ✅ DO NOT auto-disconnect (fixes your issue)
        };
    }

    /**
     * Send message
     */
    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.warn('⚠️ Cannot send, WebSocket not connected');
        }
    }

    /**
     * Manual disconnect (use on logout)
     */
    disconnect() {
        if (this.socket) {
            console.log('🔌 Manually closing WebSocket');
            this.manualClose = true;
            this.socket.close();
            this.socket = null;
            this.currentPath = null;
        }
    }
}

// ✅ Singleton instance
export const websocketService = new WebSocketService();