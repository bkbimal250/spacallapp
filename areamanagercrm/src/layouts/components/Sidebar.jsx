import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../modules/shared/hooks/useAuth';

const navItems = [
    { to: '/', label: 'Dashboard', icon: 'D' },
    { to: '/calllogs', label: 'Call Logs', icon: 'C' },
];

const Sidebar = ({ isOpen, onClose }) => {
    const { logout, user } = useAuth();

    const handleItemClick = () => {
        if (onClose) {
            onClose();
        }
    };

    return (
        <>
            {/* Mobile Sidebar Overlay Backdrop */}
            <div
                className={`fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs transition-opacity duration-300 lg:hidden ${
                    isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
                }`}
                onClick={onClose}
            />

            {/* Sidebar Container */}
            <aside
                className={`fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col border-r border-border/10 bg-sidebar text-textPrimary transition-transform duration-300 ease-in-out lg:static lg:z-0 lg:flex lg:w-64 lg:translate-x-0 lg:border-border lg:shrink-0 ${
                    isOpen ? 'translate-x-0 shadow-large' : '-translate-x-full lg:shadow-none'
                }`}
            >
                <div className="flex h-14 lg:h-16 items-center justify-between border-b border-border/10 px-6">
                    <span className="text-base lg:text-lg font-semibold tracking-wide text-primary">
                        Master Call 
                    </span>
                    {/* Mobile Close Button */}
                    <button
                        type="button"
                        onClick={onClose}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-white/50 hover:bg-white/10 hover:text-white active:scale-95 lg:hidden"
                        aria-label="Close sidebar"
                    >
                        ✕
                    </button>
                </div>

                <nav className="flex-1 space-y-1.5 overflow-y-auto p-4 scrollbar-thin">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            onClick={handleItemClick}
                            className={({ isActive }) => [
                                'flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 active:scale-[0.98]',
                                isActive 
                                    ? 'bg-primary text-white shadow-soft font-semibold' 
                                    : 'text-white/70 hover:bg-sidebarHover hover:text-white',
                            ].join(' ')}
                        >
                            <span className="flex h-5 w-5 items-center justify-center rounded bg-white/10 text-[10px] font-bold">
                                {item.icon}
                            </span>
                            {item.label}
                        </NavLink>
                    ))}
                </nav>

                <div className="border-t border-border/10 p-4 space-y-3">
                    <div className="rounded-xl bg-white/5 px-4 py-3">
                        <p className="truncate text-sm font-semibold text-white">{user?.full_name || 'Area Manager'}</p>
                        <p className="mt-0.5 truncate text-[11px] text-white/40">{user?.email || user?.phone_number || 'Assigned branch access'}</p>
                    </div>
                    <button
                        type="button"
                        onClick={() => {
                            handleItemClick();
                            logout();
                        }}
                        className="flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-semibold text-white/60 transition hover:bg-danger/10 hover:text-danger active:scale-[0.98]"
                    >
                        <span className="flex h-5 w-5 items-center justify-center rounded bg-white/10 text-[10px] font-bold">L</span>
                        Logout
                    </button>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;
