import React, { useEffect, useState } from 'react';
import { exportsAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import ExportButton from '../components/ExportButton'; // Your generic export trigger button
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
            setBranches(branchData.map(b => ({
                value: b.id,
                label: b.spa_name
            })));
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
                    <FileText size={16} className="text-gray-500" />
                    <span className="capitalize">{row.export_type.replace('_', ' ')}</span>
                </div>
            )
        },
        { header: 'Requested By', accessor: 'user_email' }, // Assuming serializer returns this
        {
            header: 'Filters',
            render: (row) => {
                const f = row.filters;
                if (!f || (!f.branch && !f.start_date && !f.end_date)) return <span className="text-gray-400">All Data</span>;
                return (
                    <div className="text-xs space-y-1">
                        {f.branch && (
                            <div className="flex items-center space-x-1">
                                <Badge variant="blue">Branch ID: {f.branch}</Badge>
                            </div>
                        )}
                        {(f.start_date || f.end_date) && (
                            <div className="text-gray-500 italic">
                                {f.start_date || '...'} to {f.end_date || '...'}
                            </div>
                        )}
                    </div>
                );
            }
        },
        { header: 'Date', render: (row) => formatDate(row.created_at) },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.status === 'completed' ? 'green' : row.status === 'failed' ? 'red' : 'yellow'}>
                    <span className="capitalize">{row.status}</span>
                </Badge>
            )
        },
        {
            header: 'Actions',
            render: (row) => (
                row.status === 'completed' && (
                    <button
                        onClick={() => handleDownload(row.id, row.file_name)}
                        className="text-blue-600 hover:text-blue-800 flex items-center space-x-1"
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
                <h1 className="text-2xl font-semibold text-gray-900">Data Exports</h1>
            </div>

            <div className="bg-white shadow rounded-lg p-6 space-y-4">
                <div className="flex items-center space-x-2 text-gray-900 font-medium mb-2">
                    <Filter size={18} />
                    <span>Generate New Export</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div>
                        <SearchableSelect
                            label="Branch"
                            placeholder="All Branches"
                            options={branches}
                            value={selectedBranch}
                            onChange={setSelectedBranch}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                        <input
                            type="date"
                            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm text-gray-900"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
                        <input
                            type="date"
                            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-sky-500 focus:border-sky-500 sm:text-sm text-gray-900"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />
                    </div>
                    <div>
                        <ExportButton onClick={handleGenerateExport} loading={generating} />
                    </div>
                </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
                <Table
                    columns={columns}
                    data={exportsList}
                />
            </div>
        </div>
    );
};

export default ExportHistory;
