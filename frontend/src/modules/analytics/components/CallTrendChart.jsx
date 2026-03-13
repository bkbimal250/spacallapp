import React from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

const CallTrendChart = ({ data = [], loading = false }) => {

    const formattedData = (data || []).map(item => ({
        ...item,
        displayDate: new Date(item.date).toLocaleDateString(
            'en-US',
            { day: 'numeric', month: 'short' }
        )
    }));

    return (

        <div className="relative w-full min-h-[280px]">

            {loading && (
                <div className="absolute inset-0 bg-background/70 backdrop-blur-sm z-10 flex items-center justify-center">
                    <div className="text-primary font-semibold animate-pulse">
                        Updating analytics...
                    </div>
                </div>
            )}

            <ResponsiveContainer width="100%" height={280} minWidth={0}>

                <AreaChart data={formattedData}>

                    <defs>

                        <linearGradient
                            id="callTrendGradient"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                        >

                            <stop
                                offset="5%"
                                stopColor="rgb(59 130 246)"
                                stopOpacity={0.25}
                            />

                            <stop
                                offset="95%"
                                stopColor="rgb(59 130 246)"
                                stopOpacity={0}
                            />

                        </linearGradient>

                    </defs>

                    <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="var(--border)"
                        opacity={0.4}
                    />

                    <XAxis
                        dataKey="displayDate"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
                        dy={10}
                    />

                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
                    />

                    <Tooltip
                        contentStyle={{
                            background: 'var(--card)',
                            borderRadius: '10px',
                            border: '1px solid var(--border)',
                            fontSize: '12px'
                        }}
                        labelStyle={{
                            color: 'var(--text-secondary)'
                        }}
                    />

                    <Area
                        type="monotone"
                        dataKey="count"
                        name="Total Calls"
                        stroke="rgb(59 130 246)"
                        strokeWidth={3}
                        fill="url(#callTrendGradient)"
                        activeDot={{ r: 5 }}
                    />

                </AreaChart>

            </ResponsiveContainer>

        </div>

    );

};

export default CallTrendChart;