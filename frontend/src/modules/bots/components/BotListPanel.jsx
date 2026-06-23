import React from 'react';
import { Bot, Copy, Plus, RefreshCw, Trash2 } from 'lucide-react';
import Button from '../../../shared/components/Button';
import BotStatusBadge from './BotStatusBadge';
import { botTypeLabels } from '../utils';

const BotListPanel = ({ bots = [], selectedBotId, loading, onSelect, onCreate, onClone, onDelete, onRefresh }) => (
    <aside className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
                <Bot size={18} className="text-primary" />
                <h2 className="font-semibold text-text-primary">Bots</h2>
            </div>
            <div className="flex gap-1">
                <Button type="button" variant="ghost" size="sm" onClick={onRefresh} title="Refresh bots">
                    <RefreshCw size={15} />
                </Button>
                <Button type="button" size="sm" onClick={onCreate} title="Create bot">
                    <Plus size={15} />
                </Button>
            </div>
        </div>
        <div className="divide-y divide-border max-h-[650px] overflow-y-auto">
            {loading ? (
                <div className="p-6 text-sm text-text-secondary">Loading bots...</div>
            ) : bots.length === 0 ? (
                <div className="p-6 text-sm text-text-secondary">No bots found.</div>
            ) : (
                bots.map((bot) => (
                    <div
                        key={bot.id}
                        role="button"
                        tabIndex={0}
                        onClick={() => onSelect(bot)}
                        onKeyDown={(event) => {
                            if (event.key === 'Enter') onSelect(bot);
                        }}
                        className={`w-full text-left p-4 transition ${selectedBotId === bot.id ? 'bg-primary/10' : 'hover:bg-background'}`}
                    >
                        <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                                <p className="font-semibold text-text-primary truncate">{bot.name}</p>
                                <p className="text-xs text-text-secondary truncate">{botTypeLabels[bot.bot_type] || bot.bot_type}</p>
                            </div>
                            <BotStatusBadge active={bot.is_active} />
                        </div>
                        <div className="mt-3 flex items-center justify-between gap-3">
                            <span className="text-xs text-text-muted truncate">{bot.slug}</span>
                            <div className="flex items-center gap-1">
                                <button
                                    type="button"
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        onClone(bot);
                                    }}
                                    className="rounded-md p-1 text-text-secondary hover:bg-primary/10 hover:text-primary"
                                    title="Clone bot"
                                >
                                    <Copy size={15} />
                                </button>
                                <button
                                    type="button"
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        onDelete(bot);
                                    }}
                                    className="rounded-md p-1 text-text-secondary hover:bg-danger/10 hover:text-danger"
                                    title="Delete bot"
                                >
                                    <Trash2 size={15} />
                                </button>
                            </div>
                        </div>
                    </div>
                ))
            )}
        </div>
    </aside>
);

export default BotListPanel;
