import React from 'react';
import { Mail, Phone, UserRound, MapPin, CalendarDays, Building2 } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Badge from '../../../shared/components/Badge';
import { formatDate } from '../../../shared/utils/formatDate';

const DetailItem = ({ icon, label, value }) => {
    const IconComponent = icon;

    return (
        <div className="flex items-start gap-3 rounded-lg border border-border bg-background px-4 py-3">
            <IconComponent size={18} className="mt-0.5 text-primary flex-shrink-0" />
            <div className="min-w-0">
                <p className="text-xs text-text-muted">{label}</p>
                <p className="text-sm font-medium text-text-primary break-words">
                    {value || '-'}
                </p>
            </div>
        </div>
    );
};

const UserDetails = ({ isOpen, onClose, user }) => {
    const roleLabel = user?.role ? user.role.replace('_', ' ') : '-';
    const areaBranches = user?.area_branch_names || [];

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="User Details"
        >
            {!user ? (
                <div className="py-10 text-center text-text-secondary">
                    Loading user details...
                </div>
            ) : (
                <div className="space-y-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                            <h2 className="text-xl font-semibold text-text-primary">
                                {user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Unnamed User'}
                            </h2>
                            <p className="text-sm text-text-secondary">{user.email}</p>
                        </div>
                        <Badge variant="blue" className="capitalize">
                            {roleLabel}
                        </Badge>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <DetailItem icon={Mail} label="Email" value={user.email} />
                        <DetailItem icon={Phone} label="Phone Number" value={user.phone_number} />
                        <DetailItem icon={UserRound} label="Role" value={roleLabel} />
                        <DetailItem icon={Building2} label="Branch" value={user.branch_name} />
                        <DetailItem icon={MapPin} label="Area Branches" value={areaBranches.join(', ')} />
                        <DetailItem icon={CalendarDays} label="Created At" value={formatDate(user.created_at, 'MMM dd, yyyy hh:mm a')} />
                    </div>
                </div>
            )}
        </Modal>
    );
};

export default UserDetails;
