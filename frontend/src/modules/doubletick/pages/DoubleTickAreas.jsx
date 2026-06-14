import React from 'react';
import { GitBranch, MapPin, Settings2 } from 'lucide-react';
import DoubleTickTabs from '../components/DoubleTickTabs';

const DoubleTickAreas = () => (
    <div className="space-y-6">
        <div>
            <h1 className="text-2xl font-bold text-text-primary">Area Mapping</h1>
            <p className="text-sm text-text-secondary">Configure controlled DoubleTick areas and branch visibility from Django admin until dedicated CRUD endpoints are enabled.</p>
        </div>
        <DoubleTickTabs />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-card border border-border rounded-lg p-5">
                <MapPin className="text-primary mb-3" size={24} />
                <h2 className="font-semibold mb-2">Lead Areas</h2>
                <p className="text-sm text-text-secondary">Create controlled areas such as Vashi, Bandra or Koramangala. Only confirmed areas can distribute leads.</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-5">
                <Settings2 className="text-info mb-3" size={24} />
                <h2 className="font-semibold mb-2">Aliases</h2>
                <p className="text-sm text-text-secondary">Add customer-friendly aliases such as “Vashi Sector 17” so future conversations match automatically.</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-5">
                <GitBranch className="text-success mb-3" size={24} />
                <h2 className="font-semibold mb-2">Branch Mapping</h2>
                <p className="text-sm text-text-secondary">Map each lead area to the branches that should see and claim leads from that area.</p>
            </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-5">
            <h2 className="font-semibold mb-3">Admin Setup Checklist</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-text-secondary">
                <div className="bg-background border border-border rounded-lg p-3">1. Add or verify DoubleTick channel/WABA records.</div>
                <div className="bg-background border border-border rounded-lg p-3">2. Create controlled lead areas with normalized names.</div>
                <div className="bg-background border border-border rounded-lg p-3">3. Add aliases for common customer location phrases.</div>
                <div className="bg-background border border-border rounded-lg p-3">4. Map each area to active CRM branches that receive leads.</div>
            </div>
        </div>
    </div>
);

export default DoubleTickAreas;
