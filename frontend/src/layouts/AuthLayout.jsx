import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">

            <div className="w-full max-w-md p-8 space-y-6 bg-card border border-border rounded-2xl shadow-xl">

                <Outlet />

            </div>

        </div>
    );
};

export default AuthLayout;