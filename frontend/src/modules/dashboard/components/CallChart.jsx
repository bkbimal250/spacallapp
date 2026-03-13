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

const CallChart = ({ data = [] }) => {

    return (
        <div className="bg-card border border-border p-6 rounded-2xl">

            <h3 className="text-lg font-semibold text-text-primary mb-4">
                Call Volume
            </h3>

            <div className="h-72 w-full">

                <ResponsiveContainer width="100%" height="100%">

                    <AreaChart
                        data={data}
                        margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                    >

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#374151"
                        />

                        <XAxis
                            dataKey="name"
                            stroke="#9CA3AF"
                            tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        />

                        <YAxis
                            stroke="#9CA3AF"
                            tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        />

                        <Tooltip
                            contentStyle={{
                                backgroundColor: "#1F2937",
                                border: "1px solid #374151",
                                borderRadius: "8px",
                                color: "#E5E7EB"
                            }}
                        />

                        <Area
                            type="monotone"
                            dataKey="calls"
                            stroke="#3B82F6"
                            fill="#3B82F6"
                            fillOpacity={0.15}
                            strokeWidth={2}
                        />

                    </AreaChart>

                </ResponsiveContainer>

            </div>

        </div>
    );
};

export default CallChart;