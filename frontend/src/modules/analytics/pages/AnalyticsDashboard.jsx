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

                const response = await branchesAPI.getBranches({ all: true });
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

        fetchBranches();

    }, []);

    useEffect(() => {

        const fetchAnalytics = async (isBackground = false) => {

            if (timeFilter === 'custom' && (!customDates.startDate || !customDates.endDate)) return;

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

                const [
                    peakRes,
                    overviewRes,
                    statsRes,
                    callsRes,
                    leadsRes
                ] = await Promise.all([
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
            }
            finally {
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

    return (

        <div className="space-y-6">

            {/* HEADER */}

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">

                <div className="flex items-center space-x-3">

                    <h1 className="text-2xl font-bold text-text-primary">
                        Analytics Dashboard
                    </h1>

                    <div
                        className="p-1.5 text-text-secondary hover:text-primary rounded-lg hover:bg-primary/10 transition"
                        title="Dashboard auto-refreshes every 10 seconds"
                    >
                        <RefreshCcw
                            size={18}
                            className={loading ? "animate-spin" : ""}
                        />
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
                            className="border border-border rounded-lg px-3 py-2 text-sm bg-card focus:ring-primary focus:border-primary"
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

            {/* CALL ANALYTICS */}

            <div className="space-y-4">

                <div className="flex items-center space-x-2">

                    <div className="h-4 w-1 bg-primary rounded-full"></div>

                    <h2 className="text-lg font-semibold text-text-primary">
                        Call Analytics
                    </h2>

                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    <div className="lg:col-span-2 bg-card p-6 rounded-xl border border-border shadow-sm">

                        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-6">
                            Call Volume Trends
                        </h3>

                        <CallTrendChart
                            data={callAnalytics.trends}
                            loading={loading}
                        />

                    </div>

                    <div className="bg-card p-6 rounded-xl border border-border shadow-sm">

                        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-6">
                            Peak Call Hours
                        </h3>

                        <PeakHourChart
                            data={peakData}
                            loading={loading}
                        />

                    </div>

                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                    <div className="bg-card p-6 rounded-xl border border-border shadow-sm">

                        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-6">
                            Call Type Distribution
                        </h3>

                        <ConversionChart
                            data={conversionData}
                            loading={loading}
                        />

                    </div>

                    <div className="bg-primary text-white p-8 rounded-xl shadow-lg">

                        <p className="text-sm opacity-80 uppercase tracking-wider">
                            Performance Score
                        </p>

                        <p className="text-4xl font-bold mt-2">
                            {stats.performance_score}
                            <span className="text-lg opacity-70">/100</span>
                        </p>

                        <div className="mt-6 h-2 bg-white/20 rounded-full">

                            <div
                                className="h-full bg-white rounded-full transition-all duration-700"
                                style={{ width: `${stats.performance_score}%` }}
                            />

                        </div>

                    </div>

                </div>

            </div>

            {/* LEAD ANALYTICS */}

            <div className="space-y-4 pt-6 border-t border-border">

                <div className="flex items-center space-x-2">

                    <div className="h-4 w-1 bg-success rounded-full"></div>

                    <h2 className="text-lg font-semibold text-text-primary">
                        Lead Success Analytics
                    </h2>

                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    <div className="bg-card p-6 rounded-xl border border-border shadow-sm">

                        <h3 className="text-xs font-semibold text-text-secondary uppercase mb-6">
                            Lead Conversion Funnel
                        </h3>

                        <LeadFunnelChart
                            data={leadAnalytics.funnel}
                            loading={loading}
                        />

                    </div>

                    <div className="grid grid-cols-2 gap-4">

                        <div className="bg-card p-6 rounded-xl border border-border text-center">

                            <p className="text-xs text-text-secondary uppercase">
                                Conversion Rate
                            </p>

                            <p className="text-3xl font-bold text-success mt-2">
                                {leadAnalytics.rates?.conversion_rate}%
                            </p>

                        </div>

                        <div className="bg-card p-6 rounded-xl border border-border text-center">

                            <p className="text-xs text-text-secondary uppercase">
                                Interest Rate
                            </p>

                            <p className="text-3xl font-bold text-warning mt-2">
                                {leadAnalytics.rates?.interest_rate}%
                            </p>

                        </div>

                    </div>

                </div>

            </div>

        </div>

    );

};

export default AnalyticsDashboard;