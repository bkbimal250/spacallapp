import React, { useEffect, useState } from 'react';
import { exportsAPI } from '../api';
import Table from '../../../shared/components/Table';
import Button from '../../../shared/components/Button';
import Badge from '../../../shared/components/Badge';
import ExportButton from '../components/ExportButton'; // Your generic export trigger button
import { Download, FileText } from 'lucide-react';
import { formatDate } from '../../../shared/utils/formatDate';

const ExportHistory = () => {
    const [exportsList, setExportsList] = useState([]);
    const [loading, setLoading] = useState(true);

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

    useEffect(() => {
        fetchExports();
    }, []);

    const handleGenerateExport = async () => {
        setLoading(true);
        try {
            await exportsAPI.triggerExport('call_logs'); // Defaulting to call_logs for now
            alert("Export started. Check back in a few moments.");
            fetchExports();
        } catch (error) {
            console.error("Failed to trigger export", error);
        } finally {
            setLoading(false);
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
                <ExportButton onClick={handleGenerateExport} loading={loading} />
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
