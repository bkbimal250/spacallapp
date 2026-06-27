import React, { useState, useEffect } from 'react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { branchesAPI } from '../api';
import { Search, Check } from 'lucide-react';

const BranchAssignmentModal = ({ isOpen, onClose, group, onAssign }) => {
    const [branches, setBranches] = useState([]);
    const [selectedIds, setSelectedIds] = useState([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchAllBranches = async () => {
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const allBranches = response.data.results || response.data || [];
                setBranches(allBranches);
                
                // Pre-select branches currently in this group
                const currentIds = allBranches
                    .filter(b => b.branch_group === group.id)
                    .map(b => b.id);
                setSelectedIds(currentIds);
            } catch (error) {
                console.error("Failed to fetch branches", error);
            }
        };

        if (isOpen && group) {
            fetchAllBranches();
        }
    }, [isOpen, group]);

    const handleToggle = (id) => {
        setSelectedIds(prev => 
            prev.includes(id) 
                ? prev.filter(i => i !== id) 
                : [...prev, id]
        );
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            await branchesAPI.assignBranches(group.id, selectedIds);
            onAssign(selectedIds);
            onClose();
        } catch (error) {
            console.error("Failed to assign branches", error);
        } finally {
            setLoading(false);
        }
    };

    const filteredBranches = branches.filter(b => {
        const haystack = [
            b.spa_name,
            b.code,
            b.city,
            b.area,
            b.state,
            b.address,
            b.phone,
            b.branch_group_name,
        ].filter(Boolean).join(' ').toLowerCase();
        return haystack.includes(search.toLowerCase());
    });

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Manage Branches - ${group?.name}`}
        >
            <div className="space-y-4">
                {/* Search */}
                <div className="relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                    <input
                        type="text"
                        placeholder="Search branch, city, area, spa code..."
                        className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-sm"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                {/* Branch List */}
                <div className="max-h-96 overflow-y-auto border border-border rounded-lg divide-y divide-border">
                    {filteredBranches.map(branch => {
                        const isSelected = selectedIds.includes(branch.id);
                        return (
                            <div 
                                key={branch.id}
                                onClick={() => handleToggle(branch.id)}
                                className={`flex items-center justify-between p-3 cursor-pointer transition-colors
                                    ${isSelected ? 'bg-primary/5' : 'hover:bg-card'}
                                `}
                            >
                                <div>
                                    <div className="text-sm font-medium text-text-primary">
                                        {branch.spa_name}
                                    </div>
                                    <div className="text-xs text-text-secondary">
                                        {branch.code} - {branch.city}
                                    </div>
                                </div>
                                <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors
                                    ${isSelected ? 'bg-primary border-primary text-white' : 'border-border'}
                                `}>
                                    {isSelected && <Check size={14} />}
                                </div>
                            </div>
                        );
                    })}

                    {filteredBranches.length === 0 && (
                        <div className="p-8 text-center text-text-secondary text-sm italic">
                            No branches found matching your search.
                        </div>
                    )}
                </div>

                <div className="flex justify-between items-center py-2 text-xs text-text-secondary">
                   <span>Selected: {selectedIds.length} branches</span>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                    <Button variant="secondary" onClick={onClose} disabled={loading}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} loading={loading}>
                        Save Changes
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default BranchAssignmentModal;
