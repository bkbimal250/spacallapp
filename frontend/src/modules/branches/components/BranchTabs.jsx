import React from 'react';
import { NavLink } from 'react-router-dom';
import { ROUTES } from '../../../routes/routeConfig';
import { GitBranch, Layers } from 'lucide-react';

const BranchTabs = () => {
    return (
        <div className="flex border-b border-border mb-6">
            <NavLink
                to={ROUTES.BRANCHES}
                end
                className={({ isActive }) => `
                    flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2
                    ${isActive 
                        ? 'border-primary text-primary bg-primary/5' 
                        : 'border-transparent text-text-secondary hover:text-text-primary hover:bg-card'}
                `}
            >
                <GitBranch size={16} />
                Branches
            </NavLink>
            <NavLink
                to={ROUTES.BRANCH_GROUPS}
                className={({ isActive }) => `
                    flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2
                    ${isActive 
                        ? 'border-primary text-primary bg-primary/5' 
                        : 'border-transparent text-text-secondary hover:text-text-primary hover:bg-card'}
                `}
            >
                <Layers size={16} />
                Branch Groups
            </NavLink>
        </div>
    );
};

export default BranchTabs;
