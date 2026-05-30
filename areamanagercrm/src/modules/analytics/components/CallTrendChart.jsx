import React, { useMemo } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

const CallTrendChart = React.memo(({ data = [], loading = false }) => {

    const formattedData = useMemo(() => (data || []).map(item => ({
        ...item,
        displayDate: new Date(item.date).toLocaleDateString(
            'en-US',
            { day: 'numeric', month: 'short' }
        )
    })), [data]);

    return (
        <div className="relative w-full min-h-[350px]">
            {loading && (
                <div className="absolute inset-0 bg-background/70 backdrop-blur-sm z-10 flex items-center justify-center rounded-2xl">
                    <div className="text-primary font-semibold animate-pulse">
                        Refreshing data...
                    </div>
                </div>
            )}

            <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id="callTrendGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="rgb(59 130 246)" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="rgb(59 130 246)" stopOpacity={0} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="var(--border)"
                        opacity={0.3}
                    />

                    <XAxis
                        dataKey="displayDate"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: 'var(--text-secondary)', fontWeight: 500 }}
                        dy={10}
                    />

                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: 'var(--text-secondary)', fontWeight: 500 }}
                    />

                    <Tooltip
                        contentStyle={{
                            background: "rgba(255, 255, 255, 0.9)",
                            backdropFilter: "blur(4px)",
                            border: "1px solid var(--border)",
                            borderRadius: "12px",
                            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                            fontSize: "12px",
                            fontWeight: "500"
                        }}
                    />

                    <Area
                        type="monotone"
                        dataKey="count"
                        name="Total Calls"
                        stroke="rgb(59 130 246)"
                        strokeWidth={4}
                        fill="url(#callTrendGradient)"
                        activeDot={{ r: 6, strokeWidth: 0, fill: "rgb(59 130 246)" }}
                        animationDuration={1500}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
});

export default CallTrendChart;