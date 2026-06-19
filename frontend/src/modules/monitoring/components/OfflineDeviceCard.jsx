import React from 'react';
import { AlertTriangle, Clock, MapPin } from 'lucide-react';

const OfflineDeviceCard = ({ title = 'Device Issue', deviceName, location, lastSeen, description }) => {
    return (

        <div className="bg-card border border-border rounded-xl p-4 shadow hover:bg-cardHover transition">

            <div className="flex items-start gap-3">

                {/* Icon */}
                <div className="flex-shrink-0 bg-danger/20 p-2 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-danger" />
                </div>

                {/* Content */}
                <div className="flex-1">

                    <h3 className="text-sm font-semibold text-danger">
                        {title}
                    </h3>

                    <div className="mt-2 space-y-1 text-sm">

                        {/* Device */}
                        <div className="font-semibold text-text-primary">
                            {deviceName}
                        </div>

                        {/* Location */}
                        <div className="flex items-center gap-1 text-xs text-text-secondary">
                            <MapPin size={12} />
                            {location}
                        </div>

                        {/* Last Seen */}
                        <div className="flex items-center gap-1 text-xs text-warning">
                            <Clock size={12} />
                            Last seen: {lastSeen}
                        </div>

                        {description && (
                            <div className="text-xs text-text-secondary pt-1">
                                {description}
                            </div>
                        )}

                    </div>

                </div>

            </div>

        </div>

    );
};

export default OfflineDeviceCard;
