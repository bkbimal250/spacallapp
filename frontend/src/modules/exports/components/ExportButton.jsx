import React from 'react';
import Button from '../../../shared/components/Button';
import { Download, Loader2 } from 'lucide-react';

const ExportButton = ({ onClick, loading = false }) => {

    return (
        <Button
            onClick={onClick}
            disabled={loading}
            className="flex items-center justify-center space-x-2 w-full md:w-auto"
        >

            {loading ? (
                <Loader2 size={16} className="animate-spin" />
            ) : (
                <Download size={16} />
            )}

            <span>
                {loading ? "Generating..." : "Export Data"}
            </span>

        </Button>
    );

};

export default ExportButton;