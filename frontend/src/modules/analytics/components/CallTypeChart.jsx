import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = [
    "rgb(16 185 129)", // Incoming (Success/Green)
    "rgb(59 130 246)", // Outgoing (Primary/Blue)
    "rgb(239 68 68)",  // Missed (Danger/Red)
    "rgb(245 158 11)"  // Rejected (Warning/Orange)
];

const CallTypeChart = React.memo(({ data = [], loading = false }) => {
    const safeData = data || [];

    return (
        <div className="relative w-full min-h-[300px]">
            {loading && (
                <div className="absolute inset-0 bg-background/70 backdrop-blur-sm z-10 flex items-center justify-center rounded-xl">
                    <div className="text-primary font-semibold animate-pulse">
                        Updating Distribution...
                    </div>
                </div>
            )}

            <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                    <Pie
                        data={safeData}
                        cx="50%"
                        cy="50%"
                        innerRadius={70}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                        nameKey="name"
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
                            background: "rgba(255, 255, 255, 0.9)",
                            backdropFilter: "blur(4px)",
                            border: "1px solid var(--border)",
                            borderRadius: "12px",
                            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                            fontSize: "12px"
                        }}
                    />
                    <Legend
                        verticalAlign="bottom"
                        align="center"
                        iconType="circle"
                        iconSize={8}
                        wrapperStyle={{
                            paddingTop: "20px",
                            fontSize: "12px",
                            fontWeight: "500",
                            color: "var(--text-secondary)"
                        }}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
});

export default CallTypeChart;
