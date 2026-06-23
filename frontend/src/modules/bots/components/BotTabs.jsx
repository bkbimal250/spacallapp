import React from 'react';
import { NavLink } from 'react-router-dom';
import { BarChart3, GitFork, History, Plug, Workflow } from 'lucide-react';

const tabs = [
    { to: '/bots', label: 'Overview', icon: BarChart3, end: true },
    { to: '/bots/builder', label: 'Builder', icon: Workflow },
    { to: '/bots/sessions', label: 'Sessions', icon: GitFork },
    { to: '/bots/logs', label: 'Logs', icon: History },
    { to: '/bots/integrations', label: 'Integrations', icon: Plug },
];

const BotTabs = () => (
    <div className="bg-card border border-border rounded-lg p-1 flex flex-wrap gap-1">
        {tabs.map((tab) => (
            <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.end}
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

export default BotTabs;
