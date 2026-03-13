import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

const PeakHourChart = ({ data = [], loading = false }) => {

    const safeData = data || [];

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

                <BarChart data={safeData}>

                    <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="var(--border)"
                        opacity={0.4}
                    />

                    <XAxis
                        dataKey="hour"
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fill: "var(--text-secondary)",
                            fontSize: 11
                        }}
                    />

                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fill: "var(--text-secondary)",
                            fontSize: 11
                        }}
                    />

                    <Tooltip
                        contentStyle={{
                            background: "var(--card)",
                            border: "1px solid var(--border)",
                            borderRadius: "10px",
                            fontSize: "12px"
                        }}
                        labelStyle={{
                            color: "var(--text-secondary)"
                        }}
                    />

                    <Bar
                        dataKey="calls"
                        fill="rgb(59 130 246)"
                        radius={[6, 6, 0, 0]}
                        barSize={32}
                    />

                </BarChart>

            </ResponsiveContainer>

        </div>

    );

};

export default PeakHourChart;