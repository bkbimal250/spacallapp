import React from 'react';
import { NavLink } from 'react-router-dom';
import { BarChart3, GitBranch, Inbox, Map, Send, AlertCircle } from 'lucide-react';

const tabs = [
    { to: '/doubletick', label: 'Overview', icon: BarChart3, info: 'Dashboard' },
    { to: '/doubletick/conversations', label: 'Pending Queue', icon: AlertCircle, info: 'Unmatched & incomplete' },
    { to: '/doubletick/leads', label: 'Area Leads', icon: Send, info: 'For distribution' },
    { to: '/doubletick/areas', label: 'Area Setup', icon: Map, info: 'CRM areas & aliases' },
    { to: '/doubletick/area-map', label: 'Branch Mapping', icon: GitBranch, info: 'Area to spa links' },
];

const DoubleTickTabs = () => (
    <div className="flex flex-wrap gap-1 bg-card border border-border rounded-lg p-1">
        {tabs.map((tab) => (
            <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.to === '/doubletick'}
                className={({ isActive }) =>
                    `inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition whitespace-nowrap ${
                        isActive ? 'bg-primary text-white shadow-sm' : 'text-text-secondary hover:bg-background hover:text-text-primary'
                    }`
                }
                title={tab.info}
            >
                <tab.icon size={16} />
                {tab.label}
            </NavLink>
        ))}
    </div>
);

export default DoubleTickTabs;
