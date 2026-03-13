import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

const DashboardLayout = () => {
    return (
        <div className="flex h-screen bg-background text-text-primary">

            <Sidebar />

            <div className="flex flex-col flex-1 overflow-hidden">

                <Navbar />

                <main className="flex-1 overflow-x-hidden overflow-y-auto p-6 bg-background">

                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>

                </main>

                <Footer />

            </div>

        </div>
    );
};

export default DashboardLayout;