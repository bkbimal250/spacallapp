import React, { useEffect, useState } from 'react';
import { exportsAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import ExportButton from '../components/ExportButton';
import { Download, FileText, Filter } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';
import { branchesAPI } from '../../branches/api';
import SearchableSelect from '../../../shared/components/SearchableSelect';

const ExportHistory = () => {

    const [exportsList, setExportsList] = useState([]);
    const [loading, setLoading] = useState(true);

    const [branches, setBranches] = useState([]);
    const [selectedBranch, setSelectedBranch] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const [generating, setGenerating] = useState(false);

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

            const response = await branchesAPI.getBranches();

            const branchData = response.data.results || response.data;

            setBranches(
                branchData.map(b => ({
                    value: b.id,
                    label: b.spa_name
                }))
            );

        } catch (error) {

            console.error("Failed to fetch branches", error);

        }

    };

    useEffect(() => {

        fetchExports();
        fetchBranches();

    }, []);

    const handleGenerateExport = async () => {

        setGenerating(true);

        try {

            await exportsAPI.triggerExport({
                type: 'call_logs',
                branch: selectedBranch,
                start_date: startDate,
                end_date: endDate
            });

            alert("Export generated successfully.");
            fetchExports();

        } catch (error) {

            console.error("Failed to trigger export", error);
            alert("Failed to generate export.");

        } finally {

            setGenerating(false);

        }

    };

    const handleDownload = async (id, filename) => {

        try {

            const response = await exportsAPI.downloadExport(id);

            const url = window.URL.createObjectURL(new Blob([response.data]));

            const link = document.createElement('a');

            link.href = url;
            link.setAttribute('download', filename || 'export.csv');

            document.body.appendChild(link);

            link.click();
            link.remove();

        } catch (error) {

            console.error("Failed to download export", error);
            alert("Download failed.");

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

                if (!f || (!f.branch && !f.start_date && !f.end_date)) {
                    return <span className="text-text-secondary">All Data</span>;
                }

                return (

                    <div className="text-xs space-y-1">

                        {f.branch && (
                            <Badge variant="blue">
                                Branch ID: {f.branch}
                            </Badge>
                        )}

                        {(f.start_date || f.end_date) && (
                            <div className="text-text-secondary italic">
                                {f.start_date || '...'} to {f.end_date || '...'}
                            </div>
                        )}

                    </div>

                );

            }
        },

        {
            header: 'Date',
            render: (row) => formatDate(row.created_at)
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

                row.status === 'completed' && (

                    <button
                        onClick={() =>
                            handleDownload(row.id, row.file_name)
                        }
                        className="flex items-center space-x-1 text-primary hover:text-primary/80 transition"
                    >

                        <Download size={16} />
                        <span>Download</span>

                    </button>

                )

            ),
        },

    ];

    return (

        <div className="space-y-6">

            <div className="flex justify-between items-center">

                <h1 className="text-2xl font-bold text-text-primary">
                    Data Exports
                </h1>

            </div>

            {/* Generate Export */}

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
                    />

                    <div>

                        <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                            From Date
                        </label>

                        <input
                            type="date"
                            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-text-primary focus:ring-primary focus:border-primary"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />

                    </div>

                    <div>

                        <label className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wide">
                            To Date
                        </label>

                        <input
                            type="date"
                            className="w-full px-3 py-2 border border-border rounded-lg bg-background text-text-primary focus:ring-primary focus:border-primary"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />

                    </div>

                    <ExportButton
                        onClick={handleGenerateExport}
                        loading={generating}
                    />

                </div>

            </div>

            {/* Export History */}

            <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">

                {loading ? (

                    <div className="p-12 text-center text-text-secondary">

                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>

                        Loading exports...

                    </div>

                ) : (

                    <Table
                        columns={columns}
                        data={exportsList}
                    />

                )}

            </div>

        </div>

    );

};

export default ExportHistory;