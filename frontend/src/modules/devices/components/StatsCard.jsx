import React, { useEffect, useState } from 'react';
import { Smartphone, Zap, ZapOff, ShieldAlert } from 'lucide-react';
import DashboardStatsCard from '../../dashboard/components/StatsCard';
import { devicesAPI } from '../api';

const StatsCard = () => {
    const [stats, setStats] = useState({
        total: 0,
        registered: 0,
        unregistered: 0,
        online: 0,
        offline: 0,
        blocked: 0,
        inactive: 0
    });
    const [loading, setLoading] = useState(true);

    const fetchStats = async (isBackground = false) => {
        if (!isBackground) setLoading(true);
        try {
            const response = await devicesAPI.getDeviceStats();
            setStats(response.data);
        } catch (error) {
            console.error("Failed to fetch device stats", error);
        } finally {
            if (!isBackground) setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
        const interval = setInterval(() => fetchStats(true), 15000);
        return () => clearInterval(interval);
    }, []);

    const cards = [
        {
            title: "Total Devices",
            value: stats.total,
            icon: <Smartphone size={18} className="text-primary" />,
            bg: "border-primary/20",
        },
        {
            title: "Registered",
            value: stats.registered,
            icon: <Smartphone size={18} className="text-success" />,
            bg: "border-success/20",
        },
        {
            title: "Pending",
            value: stats.unregistered,
            icon: <Smartphone size={18} className="text-warning" />,
            bg: "border-warning/20",
        },
        {
            title: "Online",
            value: stats.online,
            icon: <Zap size={18} className="text-success" />,
            bg: "border-success/20",
        },
        {
            title: "Offline",
            value: stats.offline,
            icon: <ZapOff size={18} className="text-text-secondary" />,
            bg: "border-border",
        },
        {
            title: "Blocked",
            value: stats.blocked,
            icon: <ShieldAlert size={18} className="text-danger" />,
            bg: "border-danger/20",
        }
    ];

    if (loading && stats.total === 0) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
                {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="h-32 bg-card animate-pulse rounded-2xl border border-border"></div>
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
            {cards.map((card, idx) => (
                <DashboardStatsCard
                    key={idx}
                    title={card.title}
                    value={card.value}
                    icon={card.icon}
                    className={card.bg}
                />
            ))}
        </div>
    );
};

export default StatsCard;
