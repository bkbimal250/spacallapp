import React, { useState, useEffect } from 'react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import { branchesAPI } from '../api';
import { MapPin, Layers, Info, CheckCircle2, XCircle } from 'lucide-react';

const ViewGroupModal = ({ isOpen, onClose, group }) => {
    const [assignedBranches, setAssignedBranches] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchGroupBranches = async () => {
            if (!group) return;
            setLoading(true);
            try {
                const response = await branchesAPI.getBranches({ group: group.id, all: true });
                const assigned = response.data.results || response.data || [];
                setAssignedBranches(assigned);
            } catch (error) {
                console.error("Failed to fetch branches for group", error);
            } finally {
                setLoading(false);
            }
        };

        if (isOpen && group) {
            fetchGroupBranches();
        }
    }, [isOpen, group]);

    if (!group) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Group Details"
            maxWidth="max-w-2xl"
        >
            <div className="space-y-6">
                {/* Group Header Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-card/50 p-4 rounded-xl border border-border">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <Layers size={20} />
                        </div>
                        <div>
                            <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Group Name</p>
                            <p className="text-lg font-bold text-text-primary">{group.name}</p>
                        </div>
                    </div>

                    <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg ${group.is_active ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                            {group.is_active ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                        </div>
                        <div>
                            <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Status</p>
                            <p className={`font-bold ${group.is_active ? 'text-success' : 'text-danger'}`}>
                                {group.is_active ? 'Active' : 'Inactive'}
                            </p>
                        </div>
                    </div>
                    
                    {group.description && (
                        <div className="col-span-1 md:col-span-2 flex items-start gap-3 mt-2 pt-2 border-t border-border/50">
                            <div className="p-2 bg-info/10 rounded-lg text-info">
                                <Info size={20} />
                            </div>
                            <div>
                                <p className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Description</p>
                                <p className="text-sm text-text-primary mt-1">{group.description}</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Assigned Branches Section */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <h3 className="text-md font-bold text-text-primary flex items-center gap-2">
                            <MapPin size={18} className="text-primary" />
                            Assigned Branches ({assignedBranches.length})
                        </h3>
                    </div>

                    <div className="max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
                        {loading ? (
                            <div className="flex flex-col items-center justify-center py-12 text-text-secondary">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-3"></div>
                                <p className="text-sm">Fetching branches...</p>
                            </div>
                        ) : assignedBranches.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {assignedBranches.map(branch => (
                                    <div 
                                        key={branch.id}
                                        className="p-3 bg-card border border-border rounded-xl hover:border-primary/30 transition-all flex items-center gap-3"
                                    >
                                        <div className="w-8 h-8 rounded-full bg-primary/5 flex items-center justify-center text-primary text-xs font-bold shrink-0">
                                            {branch.code}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="text-sm font-semibold text-text-primary truncate">{branch.spa_name}</p>
                                            <p className="text-xs text-text-secondary truncate">{branch.city}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-8 text-center bg-card/30 border border-dashed border-border rounded-xl text-text-secondary">
                                <MapPin size={32} className="mx-auto mb-2 opacity-20" />
                                <p className="text-sm italic">No branches assigned to this group yet.</p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex justify-end pt-2 border-t border-border">
                    <Button variant="secondary" onClick={onClose}>
                        Close
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default ViewGroupModal;
