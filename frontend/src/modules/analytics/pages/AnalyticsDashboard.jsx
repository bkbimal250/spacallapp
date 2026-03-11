import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../api';
import { branchesAPI } from '../../branches/api';
import PeakHourChart from '../components/PeakHourChart';
import ConversionChart from '../components/ConversionChart';
import CallTrendChart from '../components/CallTrendChart';
import LeadFunnelChart from '../components/LeadFunnelChart';
import DateRangePicker from '../../../shared/components/DateRangePicker';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { RefreshCcw } from 'lucide-react';

import { useSearchParams } from 'react-router-dom';

const AnalyticsDashboard = () => {
    const [searchParams] = useSearchParams();
    const branchFromUrl = searchParams.get('branch');

    const [peakData, setPeakData] = useState([]);
    const [conversionData, setConversionData] = useState([]);
    const [callAnalytics, setCallAnalytics] = useState({ trends: [], daily_breakdown: [] });
    const [leadAnalytics, setLeadAnalytics] = useState({ funnel: {}, status_distribution: [], rates: {} });
    const [stats, setStats] = useState({
        missed_call_ratio: 0,
        conversion_rate: 0,
        avg_duration: 0,
        performance_score: 0
    });
    const [timeFilter, setTimeFilter] = useState('today');
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

    useEffect(() => {
        const fetchAnalytics = async (isBackground = false) => {
            if (timeFilter === 'custom' && (!customDates.startDate || !customDates.endDate)) {
                return;
            }

            if (!isBackground) setLoading(true);
            try {
                const params = {
                    time_filter: timeFilter,
                    branch: selectedBranch
                };
                if (timeFilter === 'custom') {
                    params.start_date = customDates.startDate;
                    params.end_date = customDates.endDate;
                }

                const [peakRes, overviewRes, statsRes, callsRes, leadsRes] = await Promise.all([
                    analyticsAPI.getPeakHours(params),
                    analyticsAPI.getOverview(params),
                    analyticsAPI.getStats(params),
                    analyticsAPI.getCalls(params),
                    analyticsAPI.getLeads(params)
                ]);

                setPeakData(peakRes.data || []);
                setConversionData(overviewRes.data?.conversion_rates || []);
                setCallAnalytics(callsRes.data || {});
                setLeadAnalytics(leadsRes.data || {});
                setStats(statsRes.data || {});
            } catch (error) {
                console.error("Failed to fetch analytics", error);
            } finally {
                if (!isBackground) setLoading(false);
            }
        };

        fetchAnalytics();

        const intervalId = setInterval(() => {
            fetchAnalytics(true);
        }, 10000);

        return () => clearInterval(intervalId);
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
                    <div
                        className="p-1.5 text-gray-400 hover:text-sky-600 rounded-lg hover:bg-sky-50 transition-colors cursor-default"
                        title="Dashboard auto-refreshes every 10s"
                    >
                        <RefreshCcw size={18} className={loading ? "animate-spin" : ""} />
                    </div>
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
                            <option value="yesterday">Yesterday</option>
                            <option value="last_7_days">Last 7 Days</option>
                            <option value="last_30_days">Last 30 Days</option>
                            <option value="this_month">This Month</option>
                            <option value="custom">Custom Range</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Approach 1: Call Analytics */}
            <div className="space-y-4">
                <div className="flex items-center space-x-2">
                    <div className="h-4 w-1 bg-sky-500 rounded-full"></div>
                    <h2 className="text-lg font-bold text-gray-800">Approach 1: Call Analytics</h2>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest">Call Volume Trends</h3>
                            <span className="text-[10px] font-black bg-sky-50 text-sky-600 px-2 py-1 rounded-md">DAILY DATA</span>
                        </div>
                        <CallTrendChart data={callAnalytics.trends} loading={loading} />
                    </div>
                    
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-6">Peak Performance</h3>
                        <PeakHourChart data={peakData} loading={loading} />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-6">Call Type Distribution</h3>
                        <ConversionChart data={conversionData} loading={loading} />
                    </div>
                    
                    <div className="bg-sky-600 p-8 rounded-2xl shadow-lg relative overflow-hidden group">
                        <div className="relative z-10 h-full flex flex-col justify-between">
                            <div>
                                <p className="text-sky-100 text-xs font-bold uppercase tracking-[0.2em] mb-2">Overall Quality</p>
                                <p className="text-white text-4xl font-black mb-1">{stats.performance_score}<span className="text-xl opacity-50">/100</span></p>
                                <div className="h-1.5 w-full bg-sky-800/50 rounded-full mt-4 overflow-hidden">
                                    <div 
                                        className="h-full bg-white transition-all duration-1000" 
                                        style={{ width: `${stats.performance_score}%` }}
                                    ></div>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mt-8">
                                <div className="bg-white/10 p-3 rounded-xl backdrop-blur-sm">
                                    <p className="text-sky-100 text-[10px] font-bold uppercase mb-1">Missed Ratio</p>
                                    <p className="text-white font-bold">{stats.missed_call_ratio}%</p>
                                </div>
                                <div className="bg-white/10 p-3 rounded-xl backdrop-blur-sm">
                                    <p className="text-sky-100 text-[10px] font-bold uppercase mb-1">Average Time</p>
                                    <p className="text-white font-bold">{stats.avg_duration}s</p>
                                </div>
                            </div>
                        </div>
                        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-white/5 rounded-full blur-3xl group-hover:scale-110 transition-transform duration-700"></div>
                    </div>
                </div>
            </div>

            {/* Approach 2: Lead Analytics */}
            <div className="space-y-4 pt-4 border-t border-gray-100">
                <div className="flex items-center space-x-2">
                    <div className="h-4 w-1 bg-green-500 rounded-full"></div>
                    <h2 className="text-lg font-bold text-gray-800">Approach 2: Lead Success Analytics</h2>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest">Conversion Funnel</h3>
                            <span className="text-[10px] font-black bg-green-50 text-green-600 px-2 py-1 rounded-md">SALES PIPELINE</span>
                        </div>
                        <LeadFunnelChart data={leadAnalytics.funnel} loading={loading} />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center">
                            <div className="w-16 h-16 bg-green-50 rounded-2xl flex items-center justify-center mb-4">
                                <span className="text-2xl font-black text-green-600">{leadAnalytics.rates?.conversion_rate}%</span>
                            </div>
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Final Conversion</h4>
                            <p className="text-[10px] text-gray-400">Total Leads to Confirmed Visits</p>
                        </div>
                        
                        <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center">
                            <div className="w-16 h-16 bg-orange-50 rounded-2xl flex items-center justify-center mb-4">
                                <span className="text-2xl font-black text-orange-600">{leadAnalytics.rates?.interest_rate}%</span>
                            </div>
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Interest Rate</h4>
                            <p className="text-[10px] text-gray-400">Prospects expressing interest</p>
                        </div>

                        <div className="md:col-span-2 bg-gray-900 p-6 rounded-2xl shadow-xl relative overflow-hidden">
                            <div className="relative z-10 flex items-center justify-between">
                                <div>
                                    <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest mb-1">Total Leads Managed</p>
                                    <p className="text-white text-3xl font-black">{leadAnalytics.funnel?.['Total Leads'] || 0}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest mb-1">Follow-up Efforts</p>
                                    <p className="text-green-400 text-xl font-bold">{leadAnalytics.funnel?.['Followed Up'] || 0}</p>
                                </div>
                            </div>
                            <div className="absolute inset-0 bg-gradient-to-r from-gray-800/0 to-white/5 pointer-events-none"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
