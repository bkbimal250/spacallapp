import React, { useEffect, useState, useCallback } from 'react';
import { analyticsAPI } from '../api';
import { branchesAPI } from '../../branches/api';
import PeakHourChart from '../components/PeakHourChart';
import CallTrendChart from '../components/CallTrendChart';
import CallTypeChart from '../components/CallTypeChart';
import AnalyticsFilter from '../components/AnalyticsFilter';
import { TrendingUp, Clock, PieChart as PieChartIcon } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';

const AnalyticsDashboard = () => {
    const [searchParams] = useSearchParams();
    const branchFromUrl = searchParams.get('branch');

    const [data, setData] = useState({
        peakData: [],
        callDistribution: [],
        callTrends: []
    });

    const [timeFilter, setTimeFilter] = useState('today');
    const [callType, setCallType] = useState('');
    const [customDates, setCustomDates] = useState({ startDate: '', endDate: '' });
    const [selectedBranch, setSelectedBranch] = useState(branchFromUrl || '');
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);

    // Fetch branches for the filter
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

    // Memoized date change handler
    const handleDateChange = useCallback((field, value) => {
        setCustomDates(prev => ({ ...prev, [field]: value }));
    }, []);

    // Main data fetching effect
    useEffect(() => {
        const abortController = new AbortController();

        const fetchAnalytics = async (isBackground = false) => {
            if (timeFilter === 'custom' && (!customDates.startDate || !customDates.endDate)) return;

            if (!isBackground) setLoading(true);

            try {
                const params = {
                    time_filter: timeFilter,
                    branch: selectedBranch,
                    call_type: callType,
                    signal: abortController.signal
                };

                if (timeFilter === 'custom') {
                    params.start_date = customDates.startDate;
                    params.end_date = customDates.endDate;
                }

                // Fetch all required data in parallel
                const [peakRes, overviewRes, callsRes] = await Promise.all([
                    analyticsAPI.getPeakHours(params),
                    analyticsAPI.getOverview(params),
                    analyticsAPI.getCalls(params)
                ]);

                // Batch updates into a single state change to avoid violation warnings
                setData({
                    peakData: peakRes.data || [],
                    callDistribution: overviewRes.data?.conversion_rates || [],
                    callTrends: callsRes.data?.trends || []
                });

            } catch (error) {
                if (error.name === 'CanceledError' || error.name === 'AbortError') return;
                console.error("Failed to fetch analytics", error);
            } finally {
                if (!isBackground) setLoading(false);
            }
        };

        fetchAnalytics();
        
        // Auto-refresh every 20 seconds
        const intervalId = setInterval(() => fetchAnalytics(true), 20000);

        return () => {
            abortController.abort();
            clearInterval(intervalId);
        };
    }, [timeFilter, customDates, selectedBranch, callType]);

    // Destructure for cleaner JSX
    const { peakData, callDistribution, callTrends } = data;

    return (
        <div className="max-w-[1600px] mx-auto space-y-8 p-4 md:p-6 animate-in fade-in duration-500">
            
            {/* Unified Filter Component */}
            <AnalyticsFilter 
                branches={branches}
                selectedBranch={selectedBranch}
                setSelectedBranch={setSelectedBranch}
                timeFilter={timeFilter}
                setTimeFilter={setTimeFilter}
                customDates={customDates}
                handleDateChange={handleDateChange}
                callType={callType}
                setCallType={setCallType}
                loading={loading}
            />

            {/* MAIN ANALYTICS GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* 1. CALL VOLUME TRENDS (Wide) */}
                <div className="lg:col-span-8 bg-card rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col hover:shadow-md transition-shadow">
                    <div className="p-6 border-b border-border flex items-center justify-between bg-background/50">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                <TrendingUp size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-text-primary">Call Volume Trends</h3>
                                <p className="text-xs text-text-secondary">Timeline of call frequency</p>
                            </div>
                        </div>
                    </div>
                    <div className="p-6 flex-grow min-h-[350px]">
                        <CallTrendChart data={callTrends} loading={loading} />
                    </div>
                </div>

                {/* 2. CALL TYPE DISTRIBUTION */}
                <div className="lg:col-span-4 bg-card rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col hover:shadow-md transition-shadow">
                    <div className="p-6 border-b border-border flex items-center gap-3 bg-background/50">
                        <div className="p-2 bg-success/10 rounded-lg text-success">
                            <PieChartIcon size={20} />
                        </div>
                        <div>
                            <h3 className="font-semibold text-text-primary">Call Distribution</h3>
                            <p className="text-xs text-text-secondary">Breakdown by status</p>
                        </div>
                    </div>
                    <div className="p-6 flex-grow flex items-center justify-center min-h-[350px]">
                        <CallTypeChart data={callDistribution} loading={loading} />
                    </div>
                </div>

                {/* 3. PEAK CALL HOURS (Bottom Full Width) */}
                <div className="lg:col-span-12 bg-card rounded-2xl border border-border shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                    <div className="p-6 border-b border-border flex items-center justify-between bg-background/50">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-warning/10 rounded-lg text-warning">
                                <Clock size={20} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-text-primary">Peak Call Hours</h3>
                                <p className="text-xs text-text-secondary">Hourly activity analysis</p>
                            </div>
                        </div>
                    </div>
                    <div className="p-8 min-h-[400px]">
                        <PeakHourChart data={peakData} loading={loading} />
                    </div>
                </div>

            </div>
        </div>
    );
};

export default AnalyticsDashboard;
