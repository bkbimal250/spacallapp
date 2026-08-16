import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
    ArrowLeft,
    BarChart3,
    Building2,
    CheckCircle2,
    Clock,
    Edit,
    Hash,
    Layers,
    MapPin,
    Navigation,
    PhoneCall,
    ShieldCheck,
    XCircle,
    ExternalLink,
} from 'lucide-react';
import { branchesAPI } from '../api';
import Button from '../../../shared/components/Button';
import BranchForm from '../components/BranchForm';
import OperatingHoursSection from '../components/OperatingHoursSection';

const emptyValue = '-';

const Field = ({ label, value }) => (
    <div className="space-y-1">
        <div className="text-xs font-medium uppercase tracking-wide text-text-secondary">{label}</div>
        <div className="text-sm font-medium text-text-primary break-words">{value || emptyValue}</div>
    </div>
);

const LinkField = ({ label, href }) => (
    <div className="space-y-1">
        <div className="text-xs font-medium uppercase tracking-wide text-text-secondary">{label}</div>
        {href ? (
            <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="inline-flex max-w-full items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
                <span className="truncate">{href}</span>
                <ExternalLink size={14} className="shrink-0" />
            </a>
        ) : (
            <div className="text-sm font-medium text-text-primary">{emptyValue}</div>
        )}
    </div>
);

const Section = ({ title, icon, children }) => (
    <section className="bg-card border border-border rounded-lg">
        <div className="flex items-center gap-2 border-b border-border px-5 py-4">
            <span className="text-primary">{icon}</span>
            <h2 className="text-base font-semibold text-text-primary">{title}</h2>
        </div>
        <div className="p-5">{children}</div>
    </section>
);

const StatusBadge = ({ active }) => (
    <span
        className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold ${
            active ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
        }`}
    >
        {active ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
        {active ? 'Active' : 'Inactive'}
    </span>
);

const BranchView = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useSelector((state) => state.auth);
    const [branch, setBranch] = useState(null);
    const [coverages, setCoverages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isEditOpen, setIsEditOpen] = useState(false);
    const [saving, setSaving] = useState(false);

    const canEditOperatingHours = user?.role === 'admin' || user?.role === 'super_admin';

    const fetchBranch = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const [branchRes, coveragesRes] = await Promise.allSettled([
                branchesAPI.getBranch(id),
                branchesAPI.getBranchCoverages({ object_id: id }),
            ]);

            if (branchRes.status !== 'fulfilled') {
                throw branchRes.reason;
            }

            setBranch(branchRes.value.data);
            if (coveragesRes.status === 'fulfilled') {
                const data = coveragesRes.value.data;
                setCoverages(data.results || data || []);
            } else {
                setCoverages([]);
            }
        } catch (err) {
            console.error('Failed to load branch details', err);
            setError('Could not load branch details.');
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        fetchBranch();
    }, [fetchBranch]);

    const handleUpdate = async (data) => {
        setSaving(true);
        try {
            const response = await branchesAPI.updateBranch(branch.id, data);
            setBranch(prev => ({ ...prev, ...response.data }));
            setIsEditOpen(false);
        } catch (err) {
            console.error('Failed to update branch details', err);
            window.alert('Failed to update branch.');
        } finally {
            setSaving(false);
        }
    };

    const locationLine = useMemo(() => {
        if (!branch) return emptyValue;
        return [
            branch.location_area_name || branch.area,
            branch.location_city_name || branch.city,
            branch.location_state_name || branch.state,
        ].filter(Boolean).join(', ') || emptyValue;
    }, [branch]);

    const handleOperatingHoursConfiguredChange = useCallback((count) => {
        setBranch(prev => prev ? { ...prev, operating_hours_configured: count } : prev);
    }, []);

    if (loading) {
        return (
            <div className="bg-card border border-border rounded-lg p-12 text-center text-text-secondary">
                <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
                Loading branch details...
            </div>
        );
    }

    if (error || !branch) {
        return (
            <div className="bg-card border border-border rounded-lg p-8">
                <div className="mb-4 text-sm text-danger">{error || 'Branch not found.'}</div>
                <Button className="border border-x-blue-300 bg-background text-text-primary hover:bg-muted" variant="secondary" onClick={() => navigate('/branches')}>
                    <ArrowLeft size={16} className="mr-2" />
                    Back to Branches
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                    <button
                        type="button"
                        onClick={() => navigate('/branches')}
                        className="inline-flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary"
                    >
                        <ArrowLeft size={16} />
                        Back to Branches
                    </button>
                    <div className="flex flex-wrap items-center gap-3">
                        <h1 className="text-2xl font-bold text-text-primary">{branch.spa_name}</h1>
                        <StatusBadge active={branch.is_active} />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-text-secondary">
                        <span className="inline-flex items-center gap-1.5">
                            <Hash size={14} />
                            {branch.code || emptyValue}
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                            <MapPin size={14} />
                            {locationLine}
                        </span>
                    </div>
                </div>

                <div className="flex flex-wrap gap-2">
                    <Button variant="secondary" onClick={() => navigate(`/calllogs/details?branch=${branch.id}`)}>
                        <PhoneCall size={16} className="mr-2" />
                        Call Logs
                    </Button>
                    <Button variant="secondary" onClick={() => navigate(`/analytics?branch=${branch.id}`)}>
                        <BarChart3 size={16} className="mr-2" />
                        Analytics
                    </Button>
                    <Button onClick={() => setIsEditOpen(true)}>
                        <Edit size={16} className="mr-2" />
                        Edit
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="bg-card border border-border rounded-lg p-5">
                    <div className="mb-2 flex items-center gap-2 text-text-secondary">
                        <Building2 size={18} />
                        <span className="text-sm font-medium">Branch Group</span>
                    </div>
                    <div className="text-lg font-semibold text-text-primary">{branch.branch_group_name || emptyValue}</div>
                </div>
                <div className="bg-card border border-border rounded-lg p-5">
                    <div className="mb-2 flex items-center gap-2 text-text-secondary">
                        <Navigation size={18} />
                        <span className="text-sm font-medium">Primary Area</span>
                    </div>
                    <div className="text-lg font-semibold text-text-primary">{branch.location_area_name || branch.area || emptyValue}</div>
                </div>
                <div className="bg-card border border-border rounded-lg p-5">
                    <div className="mb-2 flex items-center gap-2 text-text-secondary">
                        <ShieldCheck size={18} />
                        <span className="text-sm font-medium">Coverage Areas</span>
                    </div>
                    <div className="text-lg font-semibold text-text-primary">{coverages.length}</div>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                <Section title="Branch Details" icon={<Building2 size={18} />}>
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                        <Field label="Spa Name" value={branch.spa_name} />
                        <Field label="Branch Code" value={branch.code} />
                        <Field label="Branch Group" value={branch.branch_group_name} />
                        <Field label="Phone" value={branch.phone} />
                        <LinkField label="Google Maps Link" href={branch.shared_link} />
                        <Field label="Postal Code" value={branch.postal_code} />
                        <Field label="Status" value={branch.is_active ? 'Active' : 'Inactive'} />
                    </div>
                </Section>

                <Section title="Linked Location" icon={<MapPin size={18} />}>
                    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                        <Field label="State" value={branch.location_state_name || branch.state} />
                        <Field label="City" value={branch.location_city_name || branch.city} />
                        <Field label="Zone / Group" value={branch.location_group_name} />
                        <Field label="Area" value={branch.location_area_name || branch.area} />
                    </div>
                </Section>
            </div>

            <Section title="Address" icon={<MapPin size={18} />}>
                <p className="whitespace-pre-wrap text-sm leading-6 text-text-primary">{branch.address || emptyValue}</p>
            </Section>

            <OperatingHoursSection
                branch={branch}
                canEdit={canEditOperatingHours}
                onConfiguredChange={handleOperatingHoursConfiguredChange}
            />

            <Section title="Location Coverage" icon={<Layers size={18} />}>
                {coverages.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-border">
                            <thead>
                                <tr className="text-left text-xs font-semibold uppercase tracking-wide text-text-secondary">
                                    <th className="px-3 py-2">Area</th>
                                    <th className="px-3 py-2">City</th>
                                    <th className="px-3 py-2">Group</th>
                                    <th className="px-3 py-2">Priority</th>
                                    <th className="px-3 py-2">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border text-sm text-text-primary">
                                {coverages.map((coverage) => (
                                    <tr key={coverage.id}>
                                        <td className="px-3 py-3">{coverage.area_name || emptyValue}</td>
                                        <td className="px-3 py-3">{coverage.city_name || emptyValue}</td>
                                        <td className="px-3 py-3">{coverage.location_group_name || emptyValue}</td>
                                        <td className="px-3 py-3">{coverage.priority ?? emptyValue}</td>
                                        <td className="px-3 py-3">
                                            <StatusBadge active={coverage.is_active} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-text-secondary">
                        No additional coverage areas found for this branch.
                    </div>
                )}
            </Section>

            <Section title="Record Info" icon={<Clock size={18} />}>
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                    <Field label="Branch ID" value={branch.id} />
                    <Field label="Created At" value={branch.created_at ? new Date(branch.created_at).toLocaleString() : ''} />
                    <Field label="Updated At" value={branch.updated_at ? new Date(branch.updated_at).toLocaleString() : ''} />
                    <Field label="Location State ID" value={branch.location_state} />
                    <Field label="Location City ID" value={branch.location_city} />
                    <Field label="Location Area ID" value={branch.location_area} />
                </div>
            </Section>

            <BranchForm
                isOpen={isEditOpen}
                onClose={() => setIsEditOpen(false)}
                onSubmit={handleUpdate}
                initialData={branch}
                saving={saving}
            />
        </div>
    );
};

export default BranchView;
