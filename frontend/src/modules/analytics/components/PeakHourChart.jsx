import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts';

const PeakHourChart = React.memo(({ data = [], loading = false }) => {

    const safeData = data || [];

    return (
        <div className="relative w-full min-h-[350px]">
            {loading && (
                <div className="absolute inset-0 bg-background/70 backdrop-blur-sm z-10 flex items-center justify-center rounded-2xl">
                    <div className="text-primary font-semibold animate-pulse">
                        Analyzing traffic...
                    </div>
                </div>
            )}

            <ResponsiveContainer width="100%" height={350}>
                <BarChart data={safeData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="rgb(59 130 246)" stopOpacity={1} />
                            <stop offset="100%" stopColor="rgb(59 130 246)" stopOpacity={0.6} />
                        </linearGradient>
                    </defs>

                    <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="var(--border)"
                        opacity={0.3}
                    />

                    <XAxis
                        dataKey="hour"
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fill: "var(--text-secondary)",
                            fontSize: 12,
                            fontWeight: 500
                        }}
                        dy={10}
                    />

                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fill: "var(--text-secondary)",
                            fontSize: 12,
                            fontWeight: 500
                        }}
                    />

                    <Tooltip
                        cursor={{ fill: 'var(--primary)', opacity: 0.05 }}
                        contentStyle={{
                            background: "rgba(53, 192, 76, 0.9)",
                            backdropFilter: "blur(4px)",
                            border: "1px solid var(--border)",
                            borderRadius: "12px",
                            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                            fontSize: "12px",
                            fontWeight: "500"
                        }}
                    />

                    <Bar
                        dataKey="calls"
                        fill="url(#barGradient)"
                        radius={[8, 8, 0, 0]}
                        barSize={40}
                        animationDuration={1000}
                    >
                        {safeData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                className="hover:opacity-80 transition-opacity duration-300"
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
});

export default PeakHourChart;
