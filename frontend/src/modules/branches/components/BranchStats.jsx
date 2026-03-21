import React from 'react';
import StatsCard from '../../dashboard/components/StatsCard';
import { 
    Layout, 
    CheckCircle2, 
    XCircle,
    MapPin
} from 'lucide-react';

const BranchStats = ({ stats }) => {
    
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <StatsCard 
                title="Total Branches"
                value={stats.total}
                icon={<MapPin size={20} />}
            />

            <StatsCard 
                title="Active Branches"
                value={stats.active}
                icon={<CheckCircle2 size={20} className="text-success" />}
                className="hover:border-success/40"
            />

            <StatsCard 
                title="Inactive Branches"
                value={stats.inactive}
                icon={<XCircle size={20} className="text-danger" />}
                className="hover:border-danger/40"
            />

        </div>
    );
};

export default BranchStats;
