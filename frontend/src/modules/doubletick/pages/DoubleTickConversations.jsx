import React, { useCallback, useEffect, useState } from 'react';
import Pagination from '../../../shared/components/Pagination';
import { doubletickAPI } from '../api';
import { getCount, getList } from '../utils';
import DoubleTickTabs from '../components/DoubleTickTabs';
import ConversationFilters from '../components/ConversationFilters';
import ConversationTable from '../components/ConversationTable';
import ConversationWindow from '../window/ConversationWindow';

const pageSize = 30;

const DoubleTickConversations = () => {
    const [filters, setFilters] = useState({ status: '', pending_reason: '', requires_manual_attention: '', search: '' });
    const [conversations, setConversations] = useState([]);
    const [totalCount, setTotalCount] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState(null);

    const fetchConversations = useCallback(async () => {
        setLoading(true);
        try {
            const params = { page, page_size: pageSize };
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== '') params[key] = value;
            });
            const response = await doubletickAPI.getConversations(params);
            setConversations(getList(response));
            setTotalCount(getCount(response));
        } catch (error) {
            console.error('Failed to fetch conversations', error);
        } finally {
            setLoading(false);
        }
    }, [filters, page]);

    useEffect(() => {
        fetchConversations();
    }, [fetchConversations]);

    const reset = () => {
        setFilters({ status: '', pending_reason: '', requires_manual_attention: '', search: '' });
        setPage(1);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-text-primary">Pending Conversations</h1>
                <p className="text-sm text-text-secondary">Review incomplete chats, reply manually, match areas and qualify leads.</p>
            </div>
            <DoubleTickTabs />
            <ConversationFilters filters={filters} onChange={(next) => { setFilters(next); setPage(1); }} onReset={reset} onRefresh={fetchConversations} />
            <div className="bg-card border border-border rounded-lg overflow-hidden">
                {loading ? (
                    <div className="p-12 text-center text-text-secondary">Loading conversations...</div>
                ) : (
                    <ConversationTable conversations={conversations} onOpen={(row) => setSelectedId(row.id)} />
                )}
                <Pagination currentPage={page} totalPages={Math.ceil(totalCount / pageSize)} onPageChange={setPage} totalCount={totalCount} pageSize={pageSize} />
            </div>
            <ConversationWindow
                isOpen={Boolean(selectedId)}
                conversationId={selectedId}
                onClose={() => setSelectedId(null)}
                onChanged={fetchConversations}
            />
        </div>
    );
};

export default DoubleTickConversations;
