import React from 'react';
import Button from '../../../shared/components/Button';
import { Download } from 'lucide-react';

const ExportButton = ({ onClick, loading }) => {
    return (
        <Button onClick={onClick} disabled={loading} className="flex items-center space-x-2">
            <Download size={16} />
            <span>{loading ? 'Exporting...' : 'Export Data'}</span>
        </Button>
    );
};

export default ExportButton;
