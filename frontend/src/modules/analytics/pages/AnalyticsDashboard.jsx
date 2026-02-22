import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../api';
import { branchesAPI } from '../../branches/api';
import PeakHourChart from '../components/PeakHourChart';
import ConversionChart from '../components/ConversionChart';
import DateRangePicker from '../../../shared/components/DateRangePicker';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { RefreshCcw } from 'lucide-react';

import { useSearchParams } from 'react-router-dom';

const AnalyticsDashboard = () => {
    const [searchParams] = useSearchParams();
    const branchFromUrl = searchParams.get('branch');

    const [peakData, setPeakData] = useState([]);
    const [conversionData, setConversionData] = useState([]);
    const [stats, setStats] = useState({
        missed_call_ratio: 0,
        conversion_rate: 0,
        avg_duration: 0,
        performance_score: 0
    });
    const [timeFilter, setTimeFilter] = useState('last_7_days');
    const [customDates, setCustomDates] = useState({ startDate: '', endDate: '' });
    const [selectedBranch, setSelectedBranch] = useState(branchFromUrl || '');
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
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
        fetchBranches();
    }, []);

    const fetchAnalytics = async () => {
        if (timeFilter === 'custom' && (!customDates.startDate || !customDates.endDate)) {
            return;
        }

        setLoading(true);
        try {
            const params = {
                time_filter: timeFilter,
                branch: selectedBranch
            };
            if (timeFilter === 'custom') {
                params.start_date = customDates.startDate;
                params.end_date = customDates.endDate;
            }

            const [peakRes, overviewRes, statsRes] = await Promise.all([
                analyticsAPI.getPeakHours(params),
                analyticsAPI.getOverview(params),
                analyticsAPI.getStats(params)
            ]);

            setPeakData(peakRes.data || []);
            setConversionData(overviewRes.data?.conversion_rates || []);
            setStats(statsRes.data || {});
        } catch (error) {
            console.error("Failed to fetch analytics", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, [timeFilter, customDates, selectedBranch]);

    const handleDateChange = (field, value) => {
        setCustomDates(prev => ({ ...prev, [field]: value }));
    };

    const KPI_CARDS = [
        { label: 'Missed Call Ratio', value: `${stats.missed_call_ratio}%`, color: 'text-red-600', bg: 'bg-red-50' },
        { label: 'Conversion Rate', value: `${stats.conversion_rate}%`, color: 'text-green-600', bg: 'bg-green-50' },
        { label: 'Avg Call Duration', value: `${stats.avg_duration}s`, color: 'text-blue-600', bg: 'bg-blue-50' },
        { label: 'Performance Score', value: `${stats.performance_score}/100`, color: 'text-sky-600', bg: 'bg-sky-50' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center space-x-3">
                    <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
                    <button
                        onClick={fetchAnalytics}
                        className="p-1.5 text-gray-400 hover:text-sky-600 rounded-lg hover:bg-sky-50 transition-colors"
                        title="Refresh Dashboard"
                    >
                        <RefreshCcw size={18} className={loading ? "animate-spin" : ""} />
                    </button>
                </div>

                <div className="flex flex-wrap items-center gap-4">
                    <div className="w-64">
                        <SearchableSelect
                            placeholder="All Branches"
                            options={branches}
                            value={selectedBranch}
                            onChange={setSelectedBranch}
                        />
                    </div>

                    <div className="flex items-center space-x-2">
                        {timeFilter === 'custom' && (
                            <DateRangePicker
                                startDate={customDates.startDate}
                                endDate={customDates.endDate}
                                onChange={handleDateChange}
                            />
                        )}
                        <select
                            value={timeFilter}
                            onChange={(e) => setTimeFilter(e.target.value)}
                            className="border-gray-300 rounded-md shadow-sm focus:border-sky-500 focus:ring-sky-500 px-3 py-2 border text-sm bg-white min-w-[140px]"
                        >
                            <option value="today">Today</option>
                            <option value="last_7_days">Last 7 Days</option>
                            <option value="last_30_days">Last 30 Days</option>
                            <option value="this_month">This Month</option>
                            <option value="custom">Custom Range</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {KPI_CARDS.map((kpi, idx) => (
                    <div key={idx} className={`p-4 rounded-xl shadow-sm border border-gray-100 bg-white`}>
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{kpi.label}</p>
                        <p className={`text-2xl font-bold mt-1 ${kpi.color}`}>{loading ? '...' : kpi.value}</p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-sm font-medium text-gray-700 mb-4">Peak Calling Hours</h3>
                    <PeakHourChart data={peakData} loading={loading} />
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-sm font-medium text-gray-700 mb-4">Call Distribution</h3>
                    <ConversionChart data={conversionData} loading={loading} />
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
