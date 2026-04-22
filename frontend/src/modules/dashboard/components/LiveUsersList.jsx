import React from 'react';
import { useSelector } from 'react-redux';
import { Users, Info } from 'lucide-react';

const LiveUsersList = () => {
    const onlineUsers = useSelector((state) => state.notifications.onlineUsers);

    return (
        <div className="bg-bg-secondary rounded-xl shadow-md border border-bg-tertiary p-6 overflow-hidden">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-primary/10 rounded-lg">
                        <Users className="text-primary" size={20} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-text-primary">Logged-in Users</h3>
                        <p className="text-xs text-text-secondary">Currently online</p>
                    </div>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 bg-success/10 rounded-full">
                    <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
                    <span className="text-success text-xs font-medium uppercase tracking-wider">{onlineUsers.length} Live</span>
                </div>
            </div>

            <div 
                className="space-y-1 overflow-y-auto pr-2 custom-scrollbar"
                style={{ maxHeight: '430px', minHeight: '130px' }}
            >
                {onlineUsers.length > 0 ? (
                    onlineUsers.map((user) => (
                        <div key={user.id} className="group p-3 hover:bg-bg-tertiary transition-all duration-200 rounded-lg border border-transparent hover:border-bg-quaternary">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 flex items-center justify-center font-bold text-sm rounded-lg bg-primary/10 text-primary border border-primary/20 group-hover:scale-110 transition-transform duration-200">
                                        {user.full_name?.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                        <p className="font-semibold text-sm text-text-primary group-hover:text-primary transition-colors duration-200">
                                            {user.full_name}
                                        </p>
                                        <p className="text-xs text-text-secondary flex items-center gap-1">
                                            <span className="font-medium text-accent-purple">{user.role}</span>
                                            <span className="text-text-quaternary">•</span>
                                            <span>{user.branch || "Global"}</span>
                                        </p>
                                    </div>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <span className="text-[10px] text-text-quaternary font-medium">Log in:</span>
                                    <span className="text-[11px] font-semibold text-text-tertiary bg-bg-quaternary py-0.5 px-2 rounded-md">
                                        {user.last_login_at ? new Date(user.last_login_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="flex flex-col items-center justify-center py-12 px-4 bg-bg-tertiary/30 rounded-xl border border-dashed border-bg-quaternary">
                        <div className="p-3 bg-bg-quaternary/40 rounded-full mb-3">
                            <Info className="text-text-quaternary" size={24} />
                        </div>
                        <p className="text-text-secondary text-sm font-medium">No users online right now</p>
                        <p className="text-[11px] text-text-quaternary mt-1 text-center">Active logins will appear here in real-time</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default LiveUsersList;
