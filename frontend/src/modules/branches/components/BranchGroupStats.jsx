import React, { memo } from 'react';
import StatsCard from '../../dashboard/components/StatsCard';
import { 
    Layers, 
    Link, 
    Link2Off,
    CheckCircle2
} from 'lucide-react';

const BranchGroupStats = ({ stats }) => {
    
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <StatsCard 
                title="Total Groups"
                value={stats.totalGroups}
                icon={<Layers size={20} className="text-primary" />}
                className="hover:border-primary/40 ring-1 ring-primary/5"
            />

            <StatsCard 
                title="Assigned Branches"
                value={stats.assignedBranches}
                icon={<Link size={20} className="text-success" />}
                className="hover:border-success/40 ring-1 ring-success/5"
            />

            <StatsCard 
                title="Unassigned Branches"
                value={stats.unassignedBranches}
                icon={<Link2Off size={20} className="text-warning" />}
                className="hover:border-warning/40 ring-1 ring-warning/5"
            />

        </div>
    );
};

export default memo(BranchGroupStats);