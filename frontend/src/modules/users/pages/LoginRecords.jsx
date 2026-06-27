import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { usersAPI } from '../api';
import Table from '../../../shared/components/Table';
import Badge from '../../../shared/components/Badge';
import { formatDate } from '../../../shared/utils/formatDate';
import { PageSpinner } from '../../../shared/components/loaders';
import Pagination from '../../../shared/components/Pagination';
import Button from '../../../shared/components/Button';
import { ArrowLeft } from 'lucide-react';
import { ROUTES } from '../../../routes/routeConfig';

const LoginRecords = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const userId = searchParams.get('user');
    const userName = searchParams.get('name');
    
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const pageSize = 50;

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const params = { page };
            if (userId) params.user = userId;
            
            const response = await usersAPI.getLoginHistory(params);
            if (response.data.results) {
                setRecords(response.data.results);
                setTotalCount(response.data.count);
            } else {
                setRecords(response.data);
                setTotalCount(response.data.length);
            }
        } catch (error) {
            console.error("Failed to fetch login history", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [userId, page]);

    useEffect(() => {
        setPage(1);
    }, [userId]);

    const columns = [
        {
            header: 'User',
            render: (row) => (
                <div className="flex flex-col">
                    <span className="text-text-primary font-medium">{row.user_name}</span>
                    <span className="text-xs text-text-secondary">{row.user_email}</span>
                </div>
            )
        },
        {
            header: 'Role',
            render: (row) => (
                <Badge variant={row.user_role === 'super_admin' ? 'danger' : 'primary'}>
                    {(row.user_role || '').replace('_', ' ')}
                </Badge>
            )
        },
        {
            header: 'Branch',
            render: (row) => <span className="text-text-secondary">{row.branch_name}</span>
        },
        {
            header: 'IP Address',
            render: (row) => <span className="text-text-secondary font-mono text-xs">{row.ip_address || 'Unknown'}</span>
        },
        {
            header: 'User Agent',
            render: (row) => (
                <span className="text-text-muted text-xs truncate max-w-[200px]" title={row.user_agent}>
                    {row.user_agent || 'N/A'}
                </span>
            )
        },
        {
            header: 'Login Time',
            render: (row) => (
                <span className="text-text-secondary">
                    {formatDate(row.login_at)}
                </span>
            )
        },
        {
            header: 'Status',
            render: (row) => (
                <Badge variant={row.status === 'success' ? 'success' : 'danger'}>
                    {row.status}
                </Badge>
            )
        }
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-semibold text-text-primary">
                        {userId ? 'User Login History' : 'Login Records'}
                    </h1>
                    {userId && (
                        <p className="mt-1 text-sm text-text-secondary">
                            Showing history for {userName || 'selected user'}
                        </p>
                    )}
                </div>
                {userId && (
                    <Button
                        variant="secondary"
                        onClick={() => navigate(ROUTES.USERS_LOGIN_HISTORY)}
                        className="flex items-center gap-2"
                    >
                        <ArrowLeft size={16} />
                        All Login Records
                    </Button>
                )}
            </div>
            
            <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col min-h-[500px]">
                {loading && records.length === 0 ? (
                    <PageSpinner message="Loading records..." />
                ) : records.length === 0 ? (
                    <div className="p-12 text-center text-text-secondary">No login records found.</div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <Table columns={columns} data={records} />
                        </div>
                        {totalCount > pageSize && (
                            <Pagination 
                                currentPage={page}
                                totalPages={Math.ceil(totalCount / pageSize)}
                                onPageChange={setPage}
                                totalCount={totalCount}
                                pageSize={pageSize}
                            />
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default LoginRecords;
