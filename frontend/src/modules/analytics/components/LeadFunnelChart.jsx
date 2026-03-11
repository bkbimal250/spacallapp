import React from 'react';
import { BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const LeadFunnelChart = ({ data = {}, loading = false }) => {
    // Data arrives as { "Total Leads": X, "Followed Up": Y, ... }
    // Convert to array for Recharts
    const chartData = Object.entries(data).map(([name, value]) => ({
        name,
        value
    }));

    const COLORS = ['#94a3b8', '#6366f1', '#f59e0b', '#10b981'];

    return (
        <div className="h-72 relative">
            {loading && (
                <div className="absolute inset-0 bg-white/50 z-10 flex items-center justify-center">
                    <div className="animate-pulse text-sky-600 font-medium">Updating...</div>
                </div>
            )}
            <ResponsiveContainer width="100%" height="100%" minWidth={40} minHeight={40}>
                <BarChart
                    layout="vertical"
                    data={chartData}
                    margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                    <XAxis type="number" hide />
                    <YAxis 
                        dataKey="name" 
                        type="category" 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fontSize: 11, fontWeight: 600, fill: '#64748b' }}
                        width={100}
                    />
                    <Tooltip 
                        cursor={{fill: 'transparent'}}
                        contentStyle={{ 
                            borderRadius: '12px', 
                            border: 'none', 
                            boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                            fontSize: '12px'
                        }}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={25}>
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default LeadFunnelChart;
