import React from 'react';
import {
    BarChart,
    Bar,
    Cell,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

const COLORS = [
    "rgb(148 163 184)", // Total Leads
    "rgb(99 102 241)",  // Followed Up
    "rgb(245 158 11)",  // Interested
    "rgb(16 185 129)"   // Converted
];

const LeadFunnelChart = ({ data = {}, loading = false }) => {

    const chartData = Object.entries(data || {}).map(([name, value]) => ({
        name,
        value
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

                <BarChart
                    layout="vertical"
                    data={chartData}
                    margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
                >

                    <XAxis type="number" hide />

                    <YAxis
                        dataKey="name"
                        type="category"
                        axisLine={false}
                        tickLine={false}
                        width={120}
                        tick={{
                            fontSize: 12,
                            fontWeight: 600,
                            fill: "var(--text-secondary)"
                        }}
                    />

                    <Tooltip
                        cursor={{ fill: "transparent" }}
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
                        dataKey="value"
                        radius={[0, 10, 10, 0]}
                        barSize={28}
                    >

                        {chartData.map((entry, index) => (

                            <Cell
                                key={`cell-${index}`}
                                fill={COLORS[index % COLORS.length]}
                            />

                        ))}

                    </Bar>

                </BarChart>

            </ResponsiveContainer>

        </div>

    );

};

export default LeadFunnelChart;