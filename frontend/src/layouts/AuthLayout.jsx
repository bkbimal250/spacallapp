import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">

            {/* 🔵 Gradient Glow Top */}
            <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[140px]" />

            {/* 🟣 Accent Glow Bottom */}
            <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-accent-purple/10 rounded-full blur-[140px]" />

            {/* 🔷 Cyan Soft Light */}
            <div className="absolute top-[40%] left-[60%] w-[300px] h-[300px] bg-accent-cyan/10 rounded-full blur-[120px]" />

            {/* ✨ Subtle Grid Overlay (very light) */}
            <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,#ffffff_1px,transparent_1px),linear-gradient(to_bottom,#ffffff_1px,transparent_1px)] bg-[size:40px_40px]" />

            {/* Content */}
            <div className="w-full flex items-center justify-center relative z-10 px-4">
                <Outlet />
            </div>
        </div>
    );
};

export default AuthLayout;
