import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

const DashboardLayout = () => {
    const location = useLocation();
    const isBotBuilder =
        location.pathname === '/bots/builder' ||
        location.pathname === '/bots/builder/fullscreen';

    const isFullscreen = location.pathname === '/bots/builder/fullscreen';

    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

    return (
        <div className="flex h-screen w-full overflow-hidden bg-background text-text-primary">
            {!isFullscreen && (
                <Sidebar
                    collapsed={sidebarCollapsed}
                    mobileOpen={mobileSidebarOpen}
                    onMobileClose={() => setMobileSidebarOpen(false)}
                />
            )}

            <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
                {!isFullscreen && (
                    <Navbar
                        sidebarCollapsed={sidebarCollapsed}
                        onToggleSidebar={() => setSidebarCollapsed(current => !current)}
                        onOpenMobileSidebar={() => setMobileSidebarOpen(true)}
                    />
                )}

                <main
                    className={`min-h-0 min-w-0 flex-1 overflow-y-auto overflow-x-hidden bg-background ${
                        isBotBuilder ? 'p-3 sm:p-4' : 'p-3 sm:p-4 lg:p-5 xl:p-6'
                    }`}
                >
                    <div className="min-w-0 w-full">
                        <Outlet />
                    </div>
                </main>

                {!isFullscreen && <Footer />}
            </div>
        </div>
    );
};

export default DashboardLayout;