import React, { useEffect, useRef, useState } from 'react';
import { exportsAPI } from '../api';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import ExportButton from '../components/ExportButton';
import { Calendar, Download, FileText, Filter, Trash2 } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import { branchesAPI } from '../../branches/api';
import SearchableSelect from '../../../shared/components/SearchableSelect';

const toIndiaDate = (value) => {
    if (!value) return '';
    const [year, month, day] = value.split('-');
    if (!year || !month || !day) return value;
    return `${day}/${month}/${year}`;
};

const toApiDate = (value) => {
    const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return null;

    const [, day, month, year] = match;
    const parsed = new Date(Number(year), Number(month) - 1, Number(day));
    const isValid =
        parsed.getFullYear() === Number(year) &&
        parsed.getMonth() === Number(month) - 1 &&
        parsed.getDate() === Number(day);

    return isValid ? `${year}-${month}-${day}` : null;
};

const IndiaDateInput = ({ label, value, onChange }) => {
    const pickerRef = useRef(null);
    const [displayValue, setDisplayValue] = useState(toIndiaDate(value));

    useEffect(() => {
        setDisplayValue(toIndiaDate(value));
    }, [value]);

    const openPicker = () => {
        if (pickerRef.current?.showPicker) {
            pickerRef.current.showPicker();
        } else {
            pickerRef.current?.click();
        }
    };

    const handleTextChange = (event) => {
        const nextValue = event.target.value
            .replace(/[^\d/]/g, '')
            .slice(0, 10);

        setDisplayValue(nextValue);

        if (!nextValue) {
            onChange('');
            return;
        }

        const apiDate = toApiDate(nextValue);
        if (apiDate) onChange(apiDate);
    };

    return (
        <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">{label}</label>
            <div className="relative">
                <input
                    type="text"
                    inputMode="numeric"
                    placeholder="DD/MM/YYYY"
                    className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background text-text-primary placeholder:text-text-secondary focus:ring-primary focus:border-primary"
                    value={displayValue}
                    onChange={handleTextChange}
                    onBlur={() => setDisplayValue(toIndiaDate(value))}
                />
                <button
                    type="button"
                    onClick={openPicker}
                    className="absolute inset-y-0 right-2 flex items-center text-text-secondary hover:text-text-primary transition"
                    aria-label={`Open ${label} calendar`}
                >
                    <Calendar size={18} />
                </button>
                <input
                    ref={pickerRef}
                    type="date"
                    className="sr-only"
                    value={value}
                    onChange={(event) => onChange(event.target.value)}
                    tabIndex={-1}
                    aria-hidden="true"
                />
            </div>
        </div>
    );
};

const ExportHistory = () => {

    const [exportsList, setExportsList] = useState([]);
    const [loading, setLoading] = useState(true);

    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState('');
    const [groups, setGroups] = useState([]);
    const [selectedGroup, setSelectedGroup] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [generating, setGenerating] = useState(false);
    const [downloadingId, setDownloadingId] = useState(null);
    const [deletingId, setDeletingId] = useState(null);

    const fetchExports = async () => {
        setLoading(true);
        try {
            const response = await exportsAPI.getExports();
            setExportsList(response.data.results || response.data);
        } catch (error) {
            console.error("Failed to fetch exports", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchBranches = async () => {
        try {
            const response = await branchesAPI.getBranches({ all: true });
            const branchData = response.data.results || response.data;
            setBranches(
                branchData.map(b => ({
                    value: b.id,
                    label: b.spa_name,
                    searchText: [
                        b.spa_name,
                        b.code,
                        b.city,
                        b.area,
                        b.state,
                        b.address,
                        b.phone,
                        b.branch_group_name,
                    ].filter(Boolean).join(' ')
                }))
            );
        } catch (error) {
            console.error("Failed to fetch branches", error);
        }
    };

    const fetchGroups = async () => {
        try {
            const response = await branchesAPI.getGroups({ all: true });
            const groupData = response.data.results || response.data;
            setGroups(
                groupData.map(g => ({
                    value: g.id,
                    label: g.name
                }))
            );
        } catch (error) {
            console.error("Failed to fetch groups", error);
        }
    };

    useEffect(() => {
        fetchExports();
        fetchBranches();
        fetchGroups();
    }, []);

    const handleGenerateExport = async () => {
        setGenerating(true);
        try {
            await exportsAPI.triggerExport({
                type: 'call_logs',
                branch: selectedBranch,
                group: selectedGroup,
                start_date: startDate,
                end_date: endDate
            });
            alert("Export job created successfully. Check history below.");
            fetchExports();
        } catch (error) {
            console.error("Failed to trigger export", error);
            alert("Failed to generate export.");
        } finally {
            setGenerating(false);
        }
    };

    const getDownloadFilename = (response, fallback) => {
        const disposition = response.headers?.['content-disposition'];
        const match = disposition?.match(/filename="?([^";]+)"?/i);
        return decodeURIComponent(match?.[1] || fallback || 'export.xlsx');
    };

    const getDownloadErrorMessage = async (error) => {
        const data = error.response?.data;
        if (data instanceof Blob) {
            try {
                const text = await data.text();
                const parsed = JSON.parse(text);
                return parsed.error || parsed.detail || "Download failed.";
            } catch {
                return "Download failed.";
            }
        }
        return data?.error || data?.detail || "Download failed.";
    };

    const handleDownload = async (id, filename) => {
        setDownloadingId(id);
        let url;
        try {
            const response = await exportsAPI.downloadExport(id);
            url = window.URL.createObjectURL(response.data);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', getDownloadFilename(response, filename));
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Failed to download export", error);
            alert(await getDownloadErrorMessage(error));
        } finally {
            if (url) window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
            setDownloadingId(null);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Delete this export file and history record?")) return;

        setDeletingId(id);
        try {
            await exportsAPI.deleteExport(id);
            setExportsList((items) => items.filter((item) => item.id !== id));
        } catch (error) {
            console.error("Failed to delete export", error);
            alert(error.response?.data?.error || error.response?.data?.detail || "Delete failed.");
        } finally {
            setDeletingId(null);
        }
    };

    const columns = [
        {
            header: 'Type',
            render: (row) => (
                <div className="flex items-center space-x-2">
                    <FileText size={16} className="text-text-secondary" />
                    <span className="capitalize text-text-primary">
                        {row.export_type.replace('_', ' ')}
                    </span>
                </div>
            )
        },
        { header: 'Requested By', accessor: 'user_email' },
        {
            header: 'Filters',
            render: (row) => {
                const f = row.filters;
                if (!f || (!f.branch && !f.group && !f.start_date && !f.end_date)) {
                    return <span className="text-text-secondary">All Data</span>;
                }
                return (
                    <div className="text-xs space-y-1">
                        {f.branch && (
                            <Badge variant="blue">Branch: {branches.find(b => b.value == f.branch)?.label || f.branch}</Badge>
                        )}
                        {f.group && (
                            <Badge variant="indigo">Group: {groups.find(g => g.value == f.group)?.label || f.group}</Badge>
                        )}
                        {(f.start_date || f.end_date) && (
                            <div className="text-text-secondary italic">
                                {toIndiaDate(f.start_date) || '...'} to {toIndiaDate(f.end_date) || '...'}
                            </div>
                        )}
                    </div>
                );
            }
        },
        {
            header: 'Date',
            render: (row) => formatDate(row.created_at, 'dd/MM/yyyy')
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge
                    variant={
                        row.status === 'completed'
                            ? 'green'
                            : row.status === 'failed'
                                ? 'red'
                                : 'yellow'
                    }
                >
                    <span className="capitalize">{row.status}</span>
                </Badge>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                <div className="flex items-center gap-3">
                    {row.status === 'completed' && (
                    <button
                        onClick={() => handleDownload(row.id, row.file_name)}
                        disabled={downloadingId === row.id}
                        className="flex items-center space-x-1 text-primary hover:text-primary/80 disabled:text-text-secondary disabled:cursor-wait transition"
                    >
                        <Download size={16} />
                        <span>{downloadingId === row.id ? 'Downloading...' : 'Download'}</span>
                    </button>
                    )}
                    <button
                        onClick={() => handleDelete(row.id)}
                        disabled={deletingId === row.id}
                        className="flex items-center space-x-1 text-red-500 hover:text-red-600 disabled:text-text-secondary disabled:cursor-wait transition"
                    >
                        <Trash2 size={16} />
                        <span>{deletingId === row.id ? 'Deleting...' : 'Delete'}</span>
                    </button>
                </div>
            ),
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-text-primary">Data Exports</h1>
            </div>

            <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-center space-x-2 text-text-primary font-semibold">
                    <Filter size={18} />
                    <span>Generate New Export</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <SearchableSelect
                        label="Branch"
                        placeholder="All Branches"
                        options={branches}
                        value={selectedBranch}
                        onChange={setSelectedBranch}
                        disabled={!!selectedGroup}
                    />
                    <SearchableSelect
                        label="Branch Group"
                        placeholder="All Groups"
                        options={groups}
                        value={selectedGroup}
                        onChange={setSelectedGroup}
                        disabled={!!selectedBranch}
                    />
                    <IndiaDateInput
                        label="From Date"
                        value={startDate}
                        onChange={setStartDate}
                    />
                    <IndiaDateInput
                        label="To Date"
                        value={endDate}
                        onChange={setEndDate}
                    />
                </div>

                {selectedBranch && selectedGroup && (
                    <div className="flex items-center text-xs text-warning animate-pulse">
                        ⚠️ Please choose either a specific branch OR a group, not both.
                    </div>
                )}

                <div className="pt-2">
                    <ExportButton
                        onClick={handleGenerateExport}
                        loading={generating}
                    />
                </div>
            </div>

            <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
                {loading ? (
                    <div className="p-12 text-center text-text-secondary">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                        Loading exports...
                    </div>
                ) : (
                    <Table columns={columns} data={exportsList} />
                )}
            </div>
        </div>
    );
};

export default ExportHistory;
