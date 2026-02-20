import React from 'react';
import { AlertTriangle } from 'lucide-react';

const OfflineDeviceCard = ({ deviceName, location, lastSeen }) => {
    return (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded shadow-sm">
            <div className="flex">
                <div className="flex-shrink-0">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                </div>
                <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Device Offline</h3>
                    <div className="mt-2 text-sm text-red-700">
                        <p>
                            <span className="font-semibold">{deviceName}</span> at {location}
                        </p>
                        <p className="mt-1 text-xs">Last seen: {lastSeen}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OfflineDeviceCard;
