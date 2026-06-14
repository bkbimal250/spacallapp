import React from 'react';
import { NavLink } from 'react-router-dom';
import { BarChart3, Inbox, Map, Send } from 'lucide-react';

const tabs = [
    { to: '/doubletick', label: 'Overview', icon: BarChart3 },
    { to: '/doubletick/conversations', label: 'Conversations', icon: Inbox },
    { to: '/doubletick/leads', label: 'Area Leads', icon: Send },
    { to: '/doubletick/areas', label: 'Area Mapping', icon: Map },
];

const DoubleTickTabs = () => (
    <div className="bg-card border border-border rounded-lg p-1 flex flex-wrap gap-1">
        {tabs.map((tab) => (
            <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.to === '/doubletick'}
                className={({ isActive }) =>
                    `inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition ${
                        isActive ? 'bg-primary text-white' : 'text-text-secondary hover:bg-background hover:text-text-primary'
                    }`
                }
            >
                <tab.icon size={16} />
                {tab.label}
            </NavLink>
        ))}
    </div>
);

export default DoubleTickTabs;
