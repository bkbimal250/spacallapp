import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';

const DashboardLayout = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Prevent body scroll when sidebar drawer is open on mobile
    useEffect(() => {
        if (isSidebarOpen) {
            document.body.classList.add('overflow-hidden');
        } else {
            document.body.classList.remove('overflow-hidden');
        }
        return () => {
            document.body.classList.remove('overflow-hidden');
        };
    }, [isSidebarOpen]);

    return (
        <div className="flex h-screen overflow-hidden bg-background text-textPrimary">
            {/* Sidebar drawer for mobile & static for desktop */}
            <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
            
            <div className="flex flex-1 flex-col overflow-hidden relative">
                {/* Navbar with menu trigger */}
                <Navbar onMenuClick={() => setIsSidebarOpen(true)} />
                
                {/* Main Content Area */}
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-background p-3 sm:p-4 md:p-6 pb-16 md:pb-6 scroll-touch scrollbar-thin">
                    <div className="mx-auto max-w-[1600px] w-full">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
