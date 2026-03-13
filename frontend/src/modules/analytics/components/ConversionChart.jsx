import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = [
    "rgb(16 185 129)", // Incoming
    "rgb(59 130 246)", // Outgoing
    "rgb(239 68 68)",  // Missed
    "rgb(245 158 11)"  // Rejected
];

const ConversionChart = ({ data = [], loading = false }) => {

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

                <PieChart>

                    <Pie
                        data={safeData}
                        cx="50%"
                        cy="50%"
                        innerRadius={65}
                        outerRadius={95}
                        paddingAngle={4}
                        dataKey="value"
                        stroke="none"
                    >

                        {safeData.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={COLORS[index % COLORS.length]}
                            />
                        ))}

                    </Pie>

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

                    <Legend
                        iconType="circle"
                        wrapperStyle={{
                            fontSize: "12px",
                            color: "var(--text-secondary)"
                        }}
                    />

                </PieChart>

            </ResponsiveContainer>

        </div>

    );

};

export default ConversionChart;