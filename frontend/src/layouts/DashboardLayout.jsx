import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

const DashboardLayout = () => {
    const location = useLocation();
    const isBotBuilder = location.pathname === '/bots/builder' || location.pathname === '/bots/builder/fullscreen';
    const isFullscreen = location.pathname === '/bots/builder/fullscreen';

    return (
        <div className="flex h-screen bg-background text-text-primary">

            {!isFullscreen && <Sidebar />}

            <div className="flex flex-col flex-1 overflow-hidden">

                {!isFullscreen && <Navbar />}

                <main className={`flex-1 overflow-x-hidden overflow-y-auto bg-background ${isBotBuilder ? 'p-4' : 'p-6'}`}>

                    <div className={isBotBuilder ? 'w-full' : 'max-w-7xl mx-auto'}>
                        <Outlet />
                    </div>

                </main>

                {!isFullscreen && <Footer />}

            </div>

        </div>
    );
};

export default DashboardLayout;
