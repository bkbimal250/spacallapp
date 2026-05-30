import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../modules/shared/hooks/useAuth';

const Navbar = ({ onMenuClick }) => {
    const { user, logout } = useAuth();

    return (
        <header className="sticky top-0 z-40 flex h-14 lg:h-16 items-center justify-between border-b border-border bg-sidebar px-4 lg:px-6">
            <div className="flex items-center gap-1.5">
                {/* Mobile Hamburger Trigger */}
                <button
                    type="button"
                    onClick={onMenuClick}
                    className="flex h-9 w-9 items-center justify-center rounded-lg text-white/80 hover:bg-white/10 hover:text-white active:scale-95 lg:hidden transition-all"
                    aria-label="Open Sidebar"
                >
                    <svg
                        className="h-5 w-5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth="2.5"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M4 6h16M4 12h16M4 18h16"
                        />
                    </svg>
                </button>

                <div className="flex flex-col pl-1 lg:pl-0">
                    <span className="text-xs lg:text-sm font-semibold text-white truncate max-w-[120px] xs:max-w-[160px] sm:max-w-none">
                        {user?.full_name || 'Area Manager'}
                    </span>
                    <span className="text-[10px] lg:text-xs font-medium capitalize text-primary">
                        {(user?.role || 'area_manager').replace('_', ' ')}
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-3 lg:gap-6">
                {/* Desktop-only Quick Links */}
                <Link
                    to="/calllogs"
                    className="hidden md:inline-flex rounded-lg px-3 py-2 text-xs font-semibold text-white/70 transition hover:bg-white/10 hover:text-white"
                >
                    Call Logs
                </Link>

                <div className="flex items-center gap-2 lg:gap-3 border-l border-border/40 pl-3 lg:pl-6">
                    <div className="hidden text-right md:block">
                        <p className="text-xs font-medium text-white">{user?.email || user?.phone_number}</p>
                        <p className="text-[10px] text-success font-medium">Verified</p>
                    </div>

                    <div className="flex h-8 w-8 lg:h-9 lg:w-9 items-center justify-center rounded-full bg-primary text-xs lg:text-sm font-semibold text-white select-none">
                        {user?.full_name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'A'}
                    </div>
                </div>

                {/* Desktop-only Logout Button */}
                <button
                    type="button"
                    onClick={logout}
                    className="hidden md:inline-flex rounded-lg px-3 py-2 text-xs font-semibold text-white/60 transition hover:bg-danger/10 hover:text-danger"
                >
                    Logout
                </button>
            </div>
        </header>
    );
};

export default Navbar;
