import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../api';
import PeakHourChart from '../components/PeakHourChart';
import ConversionChart from '../components/ConversionChart';
import DateRangePicker from '../../../shared/components/DateRangePicker';

const AnalyticsDashboard = () => {
    const [peakData, setPeakData] = useState([]);
    const [conversionData, setConversionData] = useState([]);
    const [timeFilter, setTimeFilter] = useState('last_7_days');
    const [customDates, setCustomDates] = useState({ startDate: '', endDate: '' });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalytics = async () => {
            if (timeFilter === 'custom' && (!customDates.startDate || !customDates.endDate)) {
                return; // Wait until both boundings are provided to invoke REST APIs.
            }

            setLoading(true);
            try {
                // Fetch dynamic arrays concurrently with active time filters
                const params = { time_filter: timeFilter };
                if (timeFilter === 'custom') {
                    params.start_date = customDates.startDate;
                    params.end_date = customDates.endDate;
                }

                const [peakRes, overviewRes] = await Promise.all([
                    analyticsAPI.getPeakHours(params),
                    analyticsAPI.getOverview(params)
                ]);

                setPeakData(peakRes.data || []);
                setConversionData(overviewRes.data?.conversion_rates || []);
            } catch (error) {
                console.error("Failed to fetch analytics", error);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalytics();
    }, [timeFilter, customDates]);

    const handleDateChange = (field, value) => {
        setCustomDates(prev => ({ ...prev, [field]: value }));
    };

    if (loading) return <div>Loading Analytics...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
                <div className="flex space-x-4 items-center">
                    {timeFilter === 'custom' && (
                        <DateRangePicker
                            startDate={customDates.startDate}
                            endDate={customDates.endDate}
                            onChange={handleDateChange}
                        />
                    )}
                    <div className="w-48">
                        <select
                            value={timeFilter}
                            onChange={(e) => setTimeFilter(e.target.value)}
                            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-2 border text-sm"
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

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PeakHourChart data={peakData} />
                <ConversionChart data={conversionData} />
            </div>
        </div>
    );
};

export default AnalyticsDashboard;
