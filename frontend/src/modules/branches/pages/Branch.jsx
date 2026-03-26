import React from 'react';
import { Outlet } from 'react-router-dom';
import BranchTabs from '../components/BranchTabs';

const Branch = () => {
    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-text-primary">
                    Branch Management
                </h1>
            </div>

            <BranchTabs />

            <div className="mt-6">
                <Outlet />
            </div>
        </div>
    );
};

export default Branch;
