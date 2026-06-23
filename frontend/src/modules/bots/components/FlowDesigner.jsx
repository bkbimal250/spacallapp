import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
    Background,
    Controls,
    Handle,
    MarkerType,
    MiniMap,
    Position,
    ReactFlow,
    useEdgesState,
    useNodesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
    GitFork, Plus, Trash2, Edit2, Play, Save, CheckCircle, AlertTriangle, 
    RefreshCw, X, ChevronRight, Settings2, PlusCircle, Sparkles, BookOpen, CheckCheck,
    MessageCircle, MousePointer2, Maximize2, Bot as BotIcon
} from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import { ROUTES } from '../../../routes/routeConfig';
import { botsAPI } from '../api';
import { formatLabel, getList, nodeTypeGroups } from '../utils';

const nodeTone = {
    start: 'bg-success/10 text-success border-success/20',
    text_message: 'bg-primary/10 text-primary border-primary/20',
    template_message: 'bg-primary/10 text-primary border-primary/20',
    question: 'bg-primary/10 text-primary border-primary/20',
    option_buttons: 'bg-primary/10 text-primary border-primary/20',
    interactive_list: 'bg-primary/10 text-primary border-primary/20',
    dynamic_city_select: 'bg-info/10 text-info border-info/20',
    dynamic_area_select: 'bg-info/10 text-info border-info/20',
    dynamic_branch_select: 'bg-info/10 text-info border-info/20',
    dynamic_state_select: 'bg-info/10 text-info border-info/20',
    match_location: 'bg-info/10 text-info border-info/20',
    api_call: 'bg-warning/10 text-warning border-warning/20',
    google_sheet_append: 'bg-warning/10 text-warning border-warning/20',
    assign_lead: 'bg-success/10 text-success border-success/20',
    broadcast_lead: 'bg-success/10 text-success border-success/20',
    round_robin_assign: 'bg-success/10 text-success border-success/20',
    manual_handover: 'bg-danger/10 text-danger border-danger/20',
    fallback: 'bg-danger/10 text-danger border-danger/20',
    end: 'bg-slate-500/10 text-slate-500 border-slate-200',
};

const graphTone = {
    start: { border: '#10b981', bg: '#ecfdf5', icon: '#10b981' },
    text_message: { border: '#6366f1', bg: '#eef2ff', icon: '#6366f1' },
    template_message: { border: '#6366f1', bg: '#eef2ff', icon: '#6366f1' },
    question: { border: '#6366f1', bg: '#eef2ff', icon: '#6366f1' },
    option_buttons: { border: '#6366f1', bg: '#eef2ff', icon: '#6366f1' },
    interactive_list: { border: '#6366f1', bg: '#eef2ff', icon: '#6366f1' },
    dynamic_state_select: { border: '#0ea5e9', bg: '#f0f9ff', icon: '#0ea5e9' },
    dynamic_city_select: { border: '#0ea5e9', bg: '#f0f9ff', icon: '#0ea5e9' },
    dynamic_area_select: { border: '#0ea5e9', bg: '#f0f9ff', icon: '#0ea5e9' },
    dynamic_branch_select: { border: '#0ea5e9', bg: '#f0f9ff', icon: '#0ea5e9' },
    match_location: { border: '#0ea5e9', bg: '#f0f9ff', icon: '#0ea5e9' },
    api_call: { border: '#f59e0b', bg: '#fffbeb', icon: '#f59e0b' },
    google_sheet_append: { border: '#f59e0b', bg: '#fffbeb', icon: '#f59e0b' },
    assign_lead: { border: '#10b981', bg: '#ecfdf5', icon: '#10b981' },
    broadcast_lead: { border: '#10b981', bg: '#ecfdf5', icon: '#10b981' },
    round_robin_assign: { border: '#10b981', bg: '#ecfdf5', icon: '#10b981' },
    manual_handover: { border: '#ef4444', bg: '#fef2f2', icon: '#ef4444' },
    fallback: { border: '#ef4444', bg: '#fef2f2', icon: '#ef4444' },
    end: { border: '#64748b', bg: '#f8fafc', icon: '#64748b' },
};

const getGraphPosition = (node, index) => {
    const saved = node.config?.canvas_position || node.config?.position;
    if (saved && Number.isFinite(Number(saved.x)) && Number.isFinite(Number(saved.y))) {
        return { x: Number(saved.x), y: Number(saved.y) };
    }
    return {
        x: (index % 3) * 360,
        y: Math.floor(index / 3) * 250,
    };
};

const buildGraph = (nodes, handlers = {}) => {
    const graphNodes = nodes.map((node, index) => ({
        id: String(node.id),
        type: 'whatsappBot',
        position: getGraphPosition(node, index),
        data: { node, ...handlers },
    }));

    const ids = new Set(nodes.map((node) => String(node.id)));
    const edges = nodes.flatMap((node) => {
        const defaultTarget = node.default_next_node && ids.has(String(node.default_next_node))
            ? [{
                id: `default-${node.id}-${node.default_next_node}`,
                source: String(node.id),
                target: String(node.default_next_node),
                sourceHandle: 'default',
                label: 'default',
                type: 'smoothstep',
                animated: true,
                markerEnd: { type: MarkerType.ArrowClosed },
                style: { stroke: '#6366f1', strokeWidth: 2 },
                labelStyle: { fill: '#475569', fontSize: 11, fontWeight: 600 },
            }]
            : [];

        const optionEdges = (node.options || [])
            .filter((option) => option.next_node && ids.has(String(option.next_node)))
            .map((option) => ({
                id: `option-${node.id}-${option.id}-${option.next_node}`,
                source: String(node.id),
                target: String(option.next_node),
                sourceHandle: `option-${option.id}`,
                label: option.label || 'choice',
                type: 'smoothstep',
                markerEnd: { type: MarkerType.ArrowClosed },
                style: { stroke: '#10b981', strokeWidth: 2 },
                labelStyle: { fill: '#0f766e', fontSize: 11, fontWeight: 700 },
            }));

        return [...defaultTarget, ...optionEdges];
    });

    return { graphNodes, edges };
};

const WhatsAppBotNode = ({ data, selected }) => {
    const node = data.node;
    const tone = graphTone[node.node_type] || graphTone.text_message;
    const options = node.options || [];

    return (
        <div
            className={`w-[290px] rounded-lg border bg-white shadow-sm transition ${selected ? 'ring-2 ring-primary/30' : ''}`}
            style={{ borderColor: tone.border }}
        >
            <Handle type="target" position={Position.Top} className="!h-3 !w-3 !border-2 !border-white !bg-slate-500" />
            <div className="rounded-t-lg px-3 py-2" style={{ backgroundColor: tone.bg }}>
                <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-2">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white shadow-sm" style={{ color: tone.icon }}>
                            <BotIcon size={17} />
                        </span>
                        <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-text-primary">{node.name || formatLabel(node.node_type)}</p>
                            <p className="truncate text-[10px] font-semibold uppercase text-text-secondary">{formatLabel(node.node_type)}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-1">
                        <button
                            type="button"
                            className="rounded-md p-1 text-text-secondary hover:bg-white hover:text-primary"
                            onClick={(event) => {
                                event.stopPropagation();
                                data.onTest(node.id);
                            }}
                            title="Test node"
                        >
                            <Play size={13} />
                        </button>
                        <button
                            type="button"
                            className="rounded-md p-1 text-text-secondary hover:bg-white hover:text-danger"
                            onClick={(event) => {
                                event.stopPropagation();
                                data.onDelete(node.id);
                            }}
                            title="Delete node"
                        >
                            <Trash2 size={13} />
                        </button>
                    </div>
                </div>
            </div>

            <div className="space-y-3 p-3">
                <div className="rounded-lg border border-border bg-[#f7fff9] p-2.5">
                    <div className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase text-[#128c7e]">
                        <MessageCircle size={12} />
                        WhatsApp message
                    </div>
                    <p className="line-clamp-4 min-h-[36px] text-xs leading-relaxed text-text-primary">
                        {node.message_text || node.preview_text || 'No message text configured.'}
                    </p>
                    <div className="mt-1 flex justify-end text-[#34b7f1]">
                        <CheckCheck size={14} />
                    </div>
                </div>

                {options.length > 0 && (
                    <div className="space-y-1.5">
                        {options.map((option) => (
                            <div key={option.id} className="relative rounded-md border border-success/20 bg-success/5 px-2 py-1.5 text-[11px] font-semibold text-success">
                                {option.label}
                                <Handle
                                    id={`option-${option.id}`}
                                    type="source"
                                    position={Position.Right}
                                    className="!right-[-7px] !h-3 !w-3 !border-2 !border-white !bg-success"
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="flex items-center justify-between border-t border-border px-3 py-2 text-[10px] text-text-secondary">
                <span>Order {node.order ?? node.position ?? 0}</span>
                <span className="font-semibold">Default route</span>
            </div>
            <Handle
                id="default"
                type="source"
                position={Position.Bottom}
                className="!h-3 !w-3 !border-2 !border-white !bg-primary"
            />
        </div>
    );
};

const nodeTypesMap = { whatsappBot: WhatsAppBotNode };

const FlowDesigner = ({ bot, onRefreshWorkspace, spacious = false }) => {
    const [flows, setFlows] = useState([]);
    const [activeFlow, setActiveFlow] = useState(null);
    const [nodes, setNodes] = useState([]);
    const [selectedNodeId, setSelectedNodeId] = useState(null);
    const [flowNodes, setFlowNodes, onFlowNodesChange] = useNodesState([]);
    const [flowEdges, setFlowEdges, onFlowEdgesChange] = useEdgesState([]);
    
    // UI states
    const [, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [nodeForm, setNodeForm] = useState(null);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    
    // Flow/Node option editors
    const [editingOption, setEditingOption] = useState(null); // option object or 'new'
    const [optionForm, setOptionForm] = useState({ label: '', value: '', payload_id: '', next_node: '', order: 0 });
    
    // Testing states
    const [testResult, setTestResult] = useState(null);
    const [testingNodeId, setTestingNodeId] = useState(null);
    const [isSimulating, setIsSimulating] = useState(false);
    const [simulationText, setSimulationText] = useState('Hello');
    const [simulationResult, setSimulationResult] = useState(null);
    const [simulatingLoading, setSimulatingLoading] = useState(false);

    // Flow Creation
    const [showCreateFlow, setShowCreateFlow] = useState(false);
    const [newFlowForm, setNewFlowForm] = useState({ name: '', version: 1 });

    const loadFlows = useCallback(async () => {
        if (!bot?.id) return;
        setLoading(true);
        try {
            const res = await botsAPI.getFlows({ bot: bot.id, all: true });
            const list = getList(res);
            setFlows(list);
            
            // Set active flow or latest version
            const active = list.find(f => f.is_active) || list[0] || null;
            setActiveFlow(active);
        } catch (err) {
            console.error('Failed to load flows', err);
            setError('Failed to fetch bot flows.');
        } finally {
            setLoading(false);
        }
    }, [bot?.id]);

    const loadNodes = useCallback(async (flowId) => {
        if (!flowId) {
            setNodes([]);
            return;
        }
        setLoading(true);
        try {
            const res = await botsAPI.getNodes({ flow: flowId, all: true });
            const list = getList(res);
            // Sort by order/position
            list.sort((a, b) => (a.order ?? a.position ?? 0) - (b.order ?? b.position ?? 0));
            setNodes(list);
        } catch (err) {
            console.error('Failed to load nodes', err);
            setError('Failed to fetch nodes for the selected flow.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadFlows();
    }, [loadFlows]);

    useEffect(() => {
        if (activeFlow?.id) {
            loadNodes(activeFlow.id);
            setSelectedNodeId(null);
            setNodeForm(null);
        } else {
            setNodes([]);
            setSelectedNodeId(null);
            setNodeForm(null);
        }
    }, [activeFlow, loadNodes]);

    const selectedNode = useMemo(() => {
        return nodes.find(n => n.id === selectedNodeId) || null;
    }, [nodes, selectedNodeId]);

    // Track changes on node form when selectedNode changes
    useEffect(() => {
        if (selectedNode) {
            setNodeForm({
                name: selectedNode.name || '',
                node_type: selectedNode.node_type || 'text_message',
                message_text: selectedNode.message_text || '',
                language: selectedNode.language || 'en',
                order: selectedNode.order ?? selectedNode.position ?? 0,
                is_active: selectedNode.is_active ?? true,
                default_next_node: selectedNode.default_next_node || '',
                config: selectedNode.config || {}
            });
            setTestResult(null);
            setEditingOption(null);
        } else {
            setNodeForm(null);
        }
    }, [selectedNode]);

    const handleCreateFlow = async (e) => {
        e.preventDefault();
        if (!newFlowForm.name.trim()) return;
        setSaving(true);
        setError('');
        try {
            const nextVersion = flows.length > 0 ? Math.max(...flows.map(f => f.version)) + 1 : 1;
            const res = await botsAPI.createFlow({
                bot: bot.id,
                name: newFlowForm.name.trim(),
                version: nextVersion,
                is_active: flows.length === 0, // make active if first flow
                config: {}
            });
            setSuccess('Flow version created successfully.');
            setShowCreateFlow(false);
            setNewFlowForm({ name: '', version: 1 });
            await loadFlows();
            setActiveFlow(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create flow.');
        } finally {
            setSaving(false);
        }
    };

    const handlePublishFlow = async (flowId) => {
        if (!window.confirm('Are you sure you want to publish this flow? This will make it active and deactivate other versions.')) return;
        setSaving(true);
        setError('');
        try {
            await botsAPI.publishFlow(flowId);
            setSuccess('Flow published and activated.');
            await loadFlows();
            if (onRefreshWorkspace) onRefreshWorkspace();
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to publish flow.');
        } finally {
            setSaving(false);
        }
    };

    const handleCreateNode = async () => {
        if (!activeFlow?.id) return;
        setSaving(true);
        setError('');
        try {
            const nextOrder = nodes.length > 0 ? Math.max(...nodes.map(n => n.order ?? n.position ?? 0)) + 10 : 10;
            const res = await botsAPI.createNode({
                flow: activeFlow.id,
                name: `New Node ${nodes.length + 1}`,
                node_type: 'text_message',
                message_text: 'Hello! How can we help you?',
                language: bot.default_language || 'en',
                order: nextOrder,
                is_active: true,
                config: {}
            });
            await loadNodes(activeFlow.id);
            setSelectedNodeId(res.data.id);
            setSuccess('Node created.');
        } catch {
            setError('Failed to create node.');
        } finally {
            setSaving(false);
        }
    };

    const handleUpdateNode = async (e) => {
        e.preventDefault();
        if (!selectedNodeId || !nodeForm) return;
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            const payload = {
                ...nodeForm,
                default_next_node: nodeForm.default_next_node || null
            };
            await botsAPI.updateNode(selectedNodeId, payload);
            setSuccess('Node saved successfully.');
            await loadNodes(activeFlow.id);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to save node.');
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteNode = useCallback(async (nodeId) => {
        if (!window.confirm('Delete this node? All option button mappings and incoming connections from this node will be disconnected.')) return;
        setSaving(true);
        setError('');
        try {
            await botsAPI.deleteNode(nodeId);
            setSuccess('Node deleted.');
            if (selectedNodeId === nodeId) {
                setSelectedNodeId(null);
                setNodeForm(null);
            }
            await loadNodes(activeFlow.id);
        } catch {
            setError('Failed to delete node.');
        } finally {
            setSaving(false);
        }
    }, [activeFlow?.id, loadNodes, selectedNodeId]);

    // Options Management
    const openAddOption = () => {
        setOptionForm({ label: '', value: '', payload_id: '', next_node: '', order: 0 });
        setEditingOption('new');
    };

    const openEditOption = (opt) => {
        setOptionForm({
            label: opt.label || '',
            value: opt.value || '',
            payload_id: opt.payload_id || '',
            next_node: opt.next_node || '',
            order: opt.order ?? 0
        });
        setEditingOption(opt);
    };

    const handleSaveOption = async (e) => {
        e.preventDefault();
        if (!selectedNodeId) return;
        setSaving(true);
        setError('');
        try {
            const payload = {
                node: selectedNodeId,
                label: optionForm.label.trim(),
                value: optionForm.value.trim() || optionForm.label.trim(),
                payload_id: optionForm.payload_id.trim() || optionForm.label.trim().toLowerCase().replace(/\s+/g, '_'),
                next_node: optionForm.next_node || null,
                order: Number(optionForm.order || 0),
                is_active: true
            };

            if (editingOption === 'new') {
                await botsAPI.createNodeOption(payload);
                setSuccess('Option created.');
            } else {
                await botsAPI.updateNodeOption(editingOption.id, payload);
                setSuccess('Option updated.');
            }
            setEditingOption(null);
            await loadNodes(activeFlow.id);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to save option.');
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteOption = async (optId) => {
        if (!window.confirm('Delete this option?')) return;
        setSaving(true);
        setError('');
        try {
            await botsAPI.deleteNodeOption(optId);
            setSuccess('Option deleted.');
            await loadNodes(activeFlow.id);
        } catch {
            setError('Failed to delete option.');
        } finally {
            setSaving(false);
        }
    };

    // Node testing
    const handleTestNode = useCallback(async (nodeId) => {
        setTestingNodeId(nodeId);
        setTestResult(null);
        try {
            const res = await botsAPI.testNode(nodeId);
            setTestResult(res.data);
        } catch {
            setError('Failed to run node test.');
        } finally {
            setTestingNodeId(null);
        }
    }, []);

    // Simulate flow execution
    const handleSimulateFlow = async (e) => {
        e.preventDefault();
        setSimulatingLoading(true);
        setSimulationResult(null);
        setError('');
        try {
            const res = await botsAPI.testFlow({
                text: simulationText
            });
            setSimulationResult(res.data);
        } catch {
            setError('Flow simulation failed. Ensure there are active flows and a lead session setup.');
        } finally {
            setSimulatingLoading(false);
        }
    };

    const handleConnect = useCallback(async ({ source, target, sourceHandle }) => {
        if (!source || !target || source === target) return;
        const sourceNode = nodes.find((node) => String(node.id) === String(source));
        if (!sourceNode) return;

        setSaving(true);
        setError('');
        setSuccess('');
        try {
            if (sourceHandle?.startsWith('option-')) {
                const optionId = sourceHandle.replace('option-', '');
                const option = (sourceNode.options || []).find((item) => String(item.id) === optionId);
                if (!option) return;
                await botsAPI.updateNodeOption(option.id, {
                    node: sourceNode.id,
                    label: option.label,
                    value: option.value || option.label,
                    payload_id: option.payload_id || String(option.label || '').toLowerCase().replace(/\s+/g, '_'),
                    next_node: target,
                    order: option.order ?? 0,
                    is_active: option.is_active ?? true,
                });
                setSuccess('Option route connected.');
            } else {
                await botsAPI.updateNode(sourceNode.id, {
                    default_next_node: target,
                });
                setSuccess('Default route connected.');
            }
            await loadNodes(activeFlow.id);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to connect route.');
        } finally {
            setSaving(false);
        }
    }, [activeFlow?.id, loadNodes, nodes]);

    const graphData = useMemo(() => buildGraph(nodes, {
        onTest: handleTestNode,
        onDelete: handleDeleteNode,
    }), [handleDeleteNode, handleTestNode, nodes]);

    useEffect(() => {
        setFlowNodes(graphData.graphNodes);
        setFlowEdges(graphData.edges);
    }, [graphData, setFlowEdges, setFlowNodes]);

    // Node type groups options
    const nodeTypes = useMemo(() => {
        const types = [];
        nodeTypeGroups.forEach(g => {
            g.items.forEach(type => {
                types.push({ type, group: g.label });
            });
        });
        return types;
    }, []);

    // Filtered lists
    const otherNodesOptions = useMemo(() => {
        return nodes
            .filter(n => n.id !== selectedNodeId)
            .map(n => ({ value: n.id, label: `${n.name} (${formatLabel(n.node_type)})` }));
    }, [nodes, selectedNodeId]);

    return (
        <div className={spacious ? 'space-y-4' : 'grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-5 items-start'}>
            
            {/* LEFT SIDEBAR: Flows & Node list */}
            <div className={spacious ? 'grid grid-cols-1 lg:grid-cols-[1fr_1fr_320px] gap-4' : 'space-y-4'}>
                
                {/* FLOW VERSION SELECTOR */}
                <div className="bg-card border border-border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-text-primary text-sm flex items-center gap-1.5">
                            <GitFork size={16} className="text-primary" />
                            Flow Version
                        </h3>
                        <Button 
                            type="button" 
                            variant="ghost" 
                            size="sm" 
                            className="p-1 h-auto text-primary" 
                            onClick={() => setShowCreateFlow(!showCreateFlow)}
                        >
                            <Plus size={16} />
                        </Button>
                    </div>

                    {showCreateFlow ? (
                        <form onSubmit={handleCreateFlow} className="space-y-3 border-t border-border pt-3">
                            <Input
                                label="Flow Name"
                                value={newFlowForm.name}
                                onChange={(e) => setNewFlowForm(prev => ({ ...prev, name: e.target.value }))}
                                placeholder="v2 Update"
                                required
                            />
                            <div className="flex gap-2 justify-end">
                                <Button type="button" variant="secondary" size="sm" onClick={() => setShowCreateFlow(false)}>
                                    Cancel
                                </Button>
                                <Button type="submit" size="sm" loading={saving}>
                                    Create
                                </Button>
                            </div>
                        </form>
                    ) : (
                        <div className="space-y-2">
                            <select
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                                value={activeFlow?.id || ''}
                                onChange={(e) => {
                                    const flow = flows.find(f => f.id === e.target.value);
                                    if (flow) setActiveFlow(flow);
                                }}
                            >
                                {flows.map(f => (
                                    <option key={f.id} value={f.id}>
                                        {f.name} (v{f.version}) {f.is_active ? '★ Active' : ''}
                                    </option>
                                ))}
                            </select>

                            {activeFlow && (
                                <div className="flex items-center justify-between text-xs pt-1">
                                    <span className="text-text-secondary">
                                        {activeFlow.is_published ? 'Published' : 'Draft'}
                                    </span>
                                    {!activeFlow.is_active && (
                                        <button
                                            type="button"
                                            className="text-primary font-medium hover:underline flex items-center gap-0.5"
                                            onClick={() => handlePublishFlow(activeFlow.id)}
                                            disabled={saving}
                                        >
                                            Publish Version
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* NODE SIDEBAR LIST */}
                <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col">
                    <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-card">
                        <span className="text-sm font-semibold text-text-primary">Flow Nodes</span>
                        <Button 
                            type="button" 
                            variant="secondary" 
                            size="sm" 
                            className="h-7 px-2 py-0"
                            onClick={handleCreateNode}
                            disabled={saving || !activeFlow}
                            title="Add new node"
                        >
                            <Plus size={14} className="mr-1" /> Add
                        </Button>
                    </div>

                    <div className="divide-y divide-border max-h-[480px] overflow-y-auto custom-scrollbar">
                        {nodes.length === 0 ? (
                            <div className="p-5 text-center text-xs text-text-secondary">
                                No nodes in this flow. Create a node to get started.
                            </div>
                        ) : (
                            nodes.map((node) => (
                                <button
                                    key={node.id}
                                    type="button"
                                    onClick={() => setSelectedNodeId(node.id)}
                                    className={`w-full text-left p-3 text-xs transition flex items-center justify-between ${
                                        selectedNodeId === node.id ? 'bg-primary/5 border-l-2 border-primary' : 'hover:bg-background'
                                    }`}
                                >
                                    <div className="min-w-0 pr-2">
                                        <div className="font-semibold text-text-primary truncate">{node.name}</div>
                                        <div className="text-[10px] text-text-muted mt-0.5 uppercase tracking-wide">
                                            {formatLabel(node.node_type)}
                                        </div>
                                    </div>
                                    <span className="shrink-0 text-[10px] bg-slate-100 text-slate-600 px-1 py-0.5 rounded font-mono">
                                        #{node.order}
                                    </span>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* TEST SIMULATION BUTTON */}
                <div className="bg-card border border-border rounded-lg p-4 space-y-3">
                    <h4 className="font-semibold text-text-primary text-sm">Flow Simulation</h4>
                    <p className="text-xs text-text-secondary">Simulate lead message replies against this bot's flows.</p>
                    <Button 
                        type="button" 
                        variant="secondary" 
                        className="w-full text-xs py-2 gap-1.5 hover-glow"
                        onClick={() => setIsSimulating(true)}
                    >
                        <Play size={14} /> Open Simulator
                    </Button>
                </div>

            </div>

            {/* CENTER: Canvas / Main view & Right Editor Drawer */}
            <div className={spacious ? 'grid grid-cols-1 2xl:grid-cols-[minmax(0,1fr)_380px] gap-4 items-start' : 'grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-5 items-start'}>
                <div className="bg-card border border-border rounded-lg overflow-hidden min-h-[680px]">
                    <div className="border-b border-border px-5 py-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                                <h2 className="font-bold text-text-primary text-lg">WhatsApp Flow Canvas</h2>
                                <p className="text-sm text-text-secondary">Drag nodes, connect handles, and inspect the full bot route structure.</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <a
                                    href={ROUTES.BOTS_BUILDER_FULLSCREEN}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-sm font-medium text-text-primary transition-all duration-150 hover:bg-background focus:outline-none"
                                >
                                    <Maximize2 size={14} />
                                    Open Full Window
                                </a>
                                <Button
                                    type="button"
                                    size="sm"
                                    className="gap-1.5"
                                    onClick={handleCreateNode}
                                    disabled={saving || !activeFlow}
                                >
                                    <Plus size={14} />
                                    Node
                                </Button>
                            </div>
                        </div>
                    </div>

                    {nodes.length === 0 ? (
                        <div className="flex min-h-[560px] flex-col items-center justify-center px-4 text-center space-y-3">
                            <Sparkles size={36} className="text-text-muted animate-pulse" />
                            <p className="text-sm text-text-secondary font-medium">Create your first node to design the bot logic.</p>
                            <Button type="button" onClick={handleCreateNode}>Create Node</Button>
                        </div>
                    ) : (
                        <div className={spacious ? 'h-[calc(100vh-310px)] min-h-[620px] bg-background' : 'h-[620px] bg-background'}>
                            <ReactFlow
                                nodes={flowNodes.map((node) => ({
                                    ...node,
                                    selected: String(node.id) === String(selectedNodeId),
                                }))}
                                edges={flowEdges}
                                nodeTypes={nodeTypesMap}
                                onNodesChange={onFlowNodesChange}
                                onEdgesChange={onFlowEdgesChange}
                                onConnect={handleConnect}
                                onNodeClick={(_, node) => setSelectedNodeId(node.id)}
                                fitView
                                fitViewOptions={{ padding: 0.2 }}
                                minZoom={0.25}
                                maxZoom={1.4}
                                proOptions={{ hideAttribution: true }}
                            >
                                <Background color="#cbd5e1" gap={18} />
                                <Controls showInteractive={false} />
                                <MiniMap
                                    pannable
                                    zoomable
                                    nodeStrokeWidth={3}
                                    nodeColor={(node) => graphTone[node.data?.node?.node_type]?.border || '#6366f1'}
                                    maskColor="rgba(248, 250, 252, 0.7)"
                                />
                                <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-lg border border-border bg-card/95 px-3 py-2 text-xs text-text-secondary shadow-sm">
                                    <MousePointer2 size={14} className="text-primary" />
                                    Drag from a node handle to another node to connect the route.
                                </div>
                            </ReactFlow>
                        </div>
                    )}
                </div>
                
                {/* FLOW BOARD PREVIEW CANVAS */}
                <div className="hidden bg-card border border-border rounded-lg p-5 min-h-[580px] space-y-5">
                    <div>
                        <h2 className="font-bold text-text-primary text-lg">Flow Connections Preview</h2>
                        <p className="text-sm text-text-secondary">Visual progression representation of nodes based on ordering and links.</p>
                    </div>

                    {nodes.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-center space-y-3">
                            <Sparkles size={36} className="text-text-muted animate-pulse" />
                            <p className="text-sm text-text-secondary font-medium">Create your first node to design the bot logic.</p>
                            <Button type="button" onClick={handleCreateNode}>Create Node</Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {nodes.map((node) => {
                                const isSelected = node.id === selectedNodeId;
                                const nextNodeObj = node.default_next_node ? nodes.find(n => n.id === node.default_next_node) : null;
                                
                                return (
                                    <div 
                                        key={node.id} 
                                        onClick={() => setSelectedNodeId(node.id)}
                                        className={`border rounded-xl p-4 transition-all duration-200 cursor-pointer ${
                                            isSelected 
                                                ? 'border-primary ring-2 ring-primary/20 shadow-md bg-primary/[0.01]' 
                                                : 'border-border bg-background/50 hover:bg-background hover:shadow-sm'
                                        }`}
                                    >
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex items-center gap-2">
                                                <span className={`inline-flex rounded-lg border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider ${
                                                    nodeTone[node.node_type] || 'bg-slate-100 text-slate-700'
                                                }`}>
                                                    {formatLabel(node.node_type)}
                                                </span>
                                                <h3 className="font-semibold text-text-primary text-sm">{node.name}</h3>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-[10px] text-text-muted">Order: {node.order}</span>
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleTestNode(node.id);
                                                    }}
                                                    className="p-1 rounded-md text-text-secondary hover:bg-primary/10 hover:text-primary transition"
                                                    title="Test node simulation"
                                                    disabled={testingNodeId === node.id}
                                                >
                                                    <Play size={13} className={testingNodeId === node.id ? 'animate-spin' : ''} />
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteNode(node.id);
                                                    }}
                                                    className="p-1 rounded-md text-text-secondary hover:bg-danger/10 hover:text-danger transition"
                                                    title="Delete node"
                                                >
                                                    <Trash2 size={13} />
                                                </button>
                                            </div>
                                        </div>

                                        {node.message_text && (
                                            <div className="mt-3 text-xs bg-card border border-border p-2.5 rounded-lg text-text-secondary italic line-clamp-2">
                                                "{node.message_text}"
                                            </div>
                                        )}

                                        {/* CONNECTIONS SUMMARY */}
                                        <div className="mt-4 pt-3 border-t border-border flex flex-wrap gap-3 items-center justify-between text-[11px] text-text-secondary">
                                            
                                            {/* OPTIONS (if any) */}
                                            {node.options && node.options.length > 0 ? (
                                                <div className="flex items-center gap-1.5 flex-wrap">
                                                    <span className="font-semibold text-text-primary">Options:</span>
                                                    {node.options.map(opt => {
                                                        const targetNode = nodes.find(n => n.id === opt.next_node);
                                                        return (
                                                            <span 
                                                                key={opt.id}
                                                                className="inline-flex items-center bg-white border border-border px-1.5 py-0.5 rounded text-[10px]"
                                                                title={`Value: ${opt.value} ➔ Goes to: ${targetNode?.name || 'End/Default'}`}
                                                            >
                                                                {opt.label} ➔ {targetNode?.name || 'End'}
                                                            </span>
                                                        );
                                                    })}
                                                </div>
                                            ) : (
                                                <span className="text-text-muted">No custom choice buttons.</span>
                                            )}

                                            {/* DEFAULT NEXT NODE */}
                                            {nextNodeObj ? (
                                                <div className="flex items-center gap-1 text-primary font-medium">
                                                    <span>Default next:</span>
                                                    <span className="underline">{nextNodeObj.name}</span>
                                                    <ChevronRight size={12} />
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-1 text-text-muted font-medium">
                                                    <span>Default next:</span>
                                                    <span>End / Halt</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* RIGHT PROPERTY EDITOR PANEL */}
                <div className="bg-card border border-border rounded-lg overflow-hidden sticky top-5 shadow-sm">
                    <div className="px-4 py-3 border-b border-border flex items-center justify-between bg-card">
                        <span className="text-sm font-semibold text-text-primary">Properties</span>
                        {selectedNodeId && (
                            <button
                                type="button"
                                className="text-xs text-text-secondary hover:text-text-primary"
                                onClick={() => setSelectedNodeId(null)}
                            >
                                Clear
                            </button>
                        )}
                    </div>

                    <div className="p-4 space-y-4 max-h-[750px] overflow-y-auto custom-scrollbar">
                        {error && (
                            <div className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
                                {error}
                            </div>
                        )}
                        {success && (
                            <div className="rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-xs text-success">
                                {success}
                            </div>
                        )}

                        {!selectedNodeId || !nodeForm ? (
                            <div className="text-center py-10 space-y-2 text-text-secondary">
                                <Settings2 size={24} className="mx-auto text-text-muted animate-pulse" />
                                <p className="text-xs">Select a node from the list or canvas to configure its settings.</p>
                            </div>
                        ) : (
                            <form onSubmit={handleUpdateNode} className="space-y-4">
                                <Input
                                    label="Node Name"
                                    value={nodeForm.name}
                                    onChange={(e) => setNodeForm(prev => ({ ...prev, name: e.target.value }))}
                                    required
                                />

                                <label className="block">
                                    <span className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wider">Node Type</span>
                                    <select
                                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm font-medium"
                                        value={nodeForm.node_type}
                                        onChange={(e) => setNodeForm(prev => ({ ...prev, node_type: e.target.value }))}
                                    >
                                        {nodeTypes.map(({ type }) => (
                                            <option key={type} value={type}>
                                                {formatLabel(type)}
                                            </option>
                                        ))}
                                    </select>
                                </label>

                                <Input
                                    label="Ordering Position"
                                    type="number"
                                    value={nodeForm.order}
                                    onChange={(e) => setNodeForm(prev => ({ ...prev, order: Number(e.target.value) }))}
                                />

                                <label className="block">
                                    <span className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wider">Message Text / Output Prompt</span>
                                    <textarea
                                        className="w-full min-h-[90px] bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary resize-none font-sans"
                                        value={nodeForm.message_text}
                                        onChange={(e) => setNodeForm(prev => ({ ...prev, message_text: e.target.value }))}
                                        placeholder="Namaste! Please select your city."
                                    />
                                    <span className="text-[10px] text-text-muted mt-1 block">Variables can be formatted as {'{var_name}'} inside message text.</span>
                                </label>

                                <Input
                                    label="Language"
                                    value={nodeForm.language}
                                    onChange={(e) => setNodeForm(prev => ({ ...prev, language: e.target.value }))}
                                    placeholder="en"
                                />

                                <label className="flex items-center gap-2 py-1">
                                    <input
                                        type="checkbox"
                                        checked={Boolean(nodeForm.is_active)}
                                        onChange={(e) => setNodeForm(prev => ({ ...prev, is_active: e.target.checked }))}
                                    />
                                    <span className="text-xs text-text-primary font-medium">Node active</span>
                                </label>

                                {/* ROUTING: DEFAULT NEXT NODE */}
                                <label className="block border-t border-border pt-3">
                                    <span className="block text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wider">Default Next Node</span>
                                    <select
                                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                                        value={nodeForm.default_next_node || ''}
                                        onChange={(e) => setNodeForm(prev => ({ ...prev, default_next_node: e.target.value }))}
                                    >
                                        <option value="">End Flow (Null)</option>
                                        {otherNodesOptions.map(opt => (
                                            <option key={opt.value} value={opt.value}>
                                                {opt.label}
                                            </option>
                                        ))}
                                    </select>
                                </label>

                                {/* DYNAMIC NODE CONFIGS */}
                                {['api_call', 'google_sheet_append', 'collect_input', 'delay', 'fallback'].includes(nodeForm.node_type) && (
                                    <div className="border-t border-border pt-4 mt-2 space-y-3">
                                        <span className="block text-xs font-bold text-text-primary uppercase tracking-wide">
                                            {formatLabel(nodeForm.node_type)} Configuration
                                        </span>

                                        {nodeForm.node_type === 'collect_input' && (
                                            <Input
                                                label="Store Input in Variable"
                                                value={nodeForm.config?.variable || ''}
                                                onChange={(e) => setNodeForm(prev => ({
                                                    ...prev,
                                                    config: { ...prev.config, variable: e.target.value }
                                                }))}
                                                placeholder="e.g. user_age"
                                            />
                                        )}

                                        {nodeForm.node_type === 'delay' && (
                                            <Input
                                                label="Delay (seconds)"
                                                type="number"
                                                value={nodeForm.config?.delay_seconds || 5}
                                                onChange={(e) => setNodeForm(prev => ({
                                                    ...prev,
                                                    config: { ...prev.config, delay_seconds: Number(e.target.value) }
                                                }))}
                                            />
                                        )}

                                        {nodeForm.node_type === 'api_call' && (
                                            <div className="space-y-3">
                                                <Input
                                                    label="Endpoint URL"
                                                    value={nodeForm.config?.url || ''}
                                                    onChange={(e) => setNodeForm(prev => ({
                                                        ...prev,
                                                        config: { ...prev.config, url: e.target.value }
                                                    }))}
                                                    placeholder="https://api.example.com/webhook"
                                                />
                                                <label className="block">
                                                    <span className="block text-xs font-semibold text-text-secondary mb-1">Method</span>
                                                    <select
                                                        className="w-full px-3 py-1.5 rounded-lg border border-border bg-background text-sm"
                                                        value={nodeForm.config?.method || 'POST'}
                                                        onChange={(e) => setNodeForm(prev => ({
                                                            ...prev,
                                                            config: { ...prev.config, method: e.target.value }
                                                        }))}
                                                    >
                                                        <option value="GET">GET</option>
                                                        <option value="POST">POST</option>
                                                        <option value="PUT">PUT</option>
                                                    </select>
                                                </label>
                                            </div>
                                        )}

                                        {nodeForm.node_type === 'google_sheet_append' && (
                                            <Input
                                                label="Google Sheet Name"
                                                value={nodeForm.config?.sheet_name || ''}
                                                onChange={(e) => setNodeForm(prev => ({
                                                    ...prev,
                                                    config: { ...prev.config, sheet_name: e.target.value }
                                                }))}
                                                placeholder="Leads Log Sheet"
                                            />
                                        )}
                                    </div>
                                )}

                                <div className="flex gap-2 justify-end border-t border-border pt-4">
                                    <Button type="submit" size="sm" className="w-full gap-1.5" loading={saving}>
                                        <Save size={14} /> Save Properties
                                    </Button>
                                </div>
                            </form>
                        )}

                        {/* BUTTONS / OPTIONS EDITOR */}
                        {selectedNodeId && ['question', 'option_buttons', 'interactive_list'].includes(selectedNode?.node_type) && (
                            <div className="border-t border-border pt-4 mt-2 space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-xs font-bold text-text-primary uppercase tracking-wide">
                                        Interactive Options
                                    </span>
                                    {!editingOption && (
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            className="p-1 h-auto text-primary"
                                            onClick={openAddOption}
                                        >
                                            <PlusCircle size={15} />
                                        </Button>
                                    )}
                                </div>

                                {editingOption ? (
                                    <form onSubmit={handleSaveOption} className="space-y-3 bg-background p-3 rounded-lg border border-border">
                                        <p className="text-[11px] font-semibold text-text-secondary">
                                            {editingOption === 'new' ? 'New Option' : 'Edit Option'}
                                        </p>
                                        <Input
                                            label="Button Label"
                                            value={optionForm.label}
                                            onChange={(e) => setOptionForm(prev => ({ ...prev, label: e.target.value }))}
                                            placeholder="Mumbai"
                                            required
                                        />
                                        <Input
                                            label="Match Value"
                                            value={optionForm.value}
                                            onChange={(e) => setOptionForm(prev => ({ ...prev, value: e.target.value }))}
                                            placeholder="Optional value"
                                        />
                                        <label className="block text-xs">
                                            <span className="block text-text-secondary mb-1">Target Next Node</span>
                                            <select
                                                className="w-full px-2.5 py-1.5 rounded-lg border border-border bg-card text-xs"
                                                value={optionForm.next_node}
                                                onChange={(e) => setOptionForm(prev => ({ ...prev, next_node: e.target.value }))}
                                            >
                                                <option value="">Default Next Node / Halt</option>
                                                {otherNodesOptions.map(opt => (
                                                    <option key={opt.value} value={opt.value}>
                                                        {opt.label}
                                                    </option>
                                                ))}
                                            </select>
                                        </label>
                                        <div className="flex justify-end gap-2 text-xs pt-1">
                                            <Button type="button" variant="secondary" size="sm" className="h-7 py-0 px-2" onClick={() => setEditingOption(null)}>
                                                Cancel
                                            </Button>
                                            <Button type="submit" size="sm" className="h-7 py-0 px-2" loading={saving}>
                                                Save Option
                                            </Button>
                                        </div>
                                    </form>
                                ) : (
                                    <div className="space-y-2">
                                        {selectedNode.options && selectedNode.options.length > 0 ? (
                                            selectedNode.options.map(opt => {
                                                const dest = nodes.find(n => n.id === opt.next_node);
                                                return (
                                                    <div key={opt.id} className="flex items-center justify-between p-2 rounded bg-background border border-border text-xs">
                                                        <div className="min-w-0 pr-1.5">
                                                            <span className="font-semibold text-text-primary block truncate">{opt.label}</span>
                                                            <span className="text-[10px] text-text-muted block truncate">
                                                                ➔ {dest?.name || 'Default next'}
                                                            </span>
                                                        </div>
                                                        <div className="flex items-center shrink-0 gap-1">
                                                            <button
                                                                type="button"
                                                                onClick={() => openEditOption(opt)}
                                                                className="p-1 hover:text-primary rounded"
                                                            >
                                                                <Edit2 size={11} />
                                                            </button>
                                                            <button
                                                                type="button"
                                                                onClick={() => handleDeleteOption(opt.id)}
                                                                className="p-1 hover:text-danger rounded"
                                                            >
                                                                <Trash2 size={11} />
                                                            </button>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <p className="text-[11px] text-text-muted italic">No options configured yet.</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* NODE TEST OUTPUT PREVIEW */}
                        {testResult && (
                            <div className="border-t border-border pt-4 mt-2 space-y-2">
                                <span className="text-xs font-bold text-text-primary uppercase tracking-wide flex items-center gap-1">
                                    <BookOpen size={14} className="text-primary" /> Test Response Preview
                                </span>
                                <div className="bg-slate-950 text-slate-200 p-3 rounded-lg text-[10px] font-mono overflow-x-auto max-w-full space-y-1">
                                    <p><span className="text-success">Node ID:</span> {testResult.node_id}</p>
                                    <p><span className="text-success">Type:</span> {testResult.node_type}</p>
                                    <p><span className="text-success">Config:</span> {JSON.stringify(testResult.config)}</p>
                                    <p className="border-t border-slate-800 pt-1.5 mt-1.5 text-info font-sans italic">
                                        Preview message:
                                    </p>
                                    <p className="font-sans text-xs bg-slate-900 p-2 rounded border border-slate-800 mt-1 whitespace-pre-wrap">
                                        {testResult.preview || 'No message output prompt set.'}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

            </div>

            {/* SIMULATOR MODAL */}
            {isSimulating && (
                <div className="fixed inset-0 z-[9999] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-fadeIn flex flex-col max-h-[90vh]">
                        <div className="px-5 py-4 border-b border-border flex items-center justify-between bg-card shrink-0">
                            <div>
                                <h3 className="font-bold text-text-primary text-base">WhatsApp Bot Execution Simulator</h3>
                                <p className="text-xs text-text-secondary">Send a simulated message to trigger active bot flow processing.</p>
                            </div>
                            <button
                                type="button"
                                className="p-1 rounded-lg text-text-muted hover:bg-slate-100 hover:text-text-primary"
                                onClick={() => {
                                    setIsSimulating(false);
                                    setSimulationResult(null);
                                }}
                            >
                                <X size={20} />
                            </button>
                        </div>

                        <div className="p-5 overflow-y-auto space-y-4 grow">
                            <form onSubmit={handleSimulateFlow} className="space-y-4">
                                <Input
                                    label="Simulated Customer Reply Message"
                                    value={simulationText}
                                    onChange={(e) => setSimulationText(e.target.value)}
                                    placeholder="Andheri"
                                    required
                                />
                                <div className="flex justify-end">
                                    <Button type="submit" loading={simulatingLoading} disabled={simulatingLoading} className="w-full">
                                        Simulate Incoming Message
                                    </Button>
                                </div>
                            </form>

                            {simulationResult && (
                                <div className="space-y-3 pt-2">
                                    <div className="flex items-center gap-2 border-t border-border pt-4">
                                        <CheckCircle size={18} className="text-success" />
                                        <span className="font-semibold text-text-primary text-sm">Engine Session Result</span>
                                    </div>
                                    
                                    <div className="grid grid-cols-2 gap-3 text-xs bg-background p-3 rounded-lg border border-border">
                                        <div>
                                            <span className="text-text-muted uppercase tracking-wider text-[9px] block">Session ID</span>
                                            <span className="font-medium text-text-primary truncate block">{simulationResult.id}</span>
                                        </div>
                                        <div>
                                            <span className="text-text-muted uppercase tracking-wider text-[9px] block">Session Status</span>
                                            <span className="font-medium text-text-primary block">{formatLabel(simulationResult.status)}</span>
                                        </div>
                                        <div>
                                            <span className="text-text-muted uppercase tracking-wider text-[9px] block">Current Node</span>
                                            <span className="font-medium text-text-primary block">{simulationResult.current_node_name || 'Halted / Completed'}</span>
                                        </div>
                                        <div>
                                            <span className="text-text-muted uppercase tracking-wider text-[9px] block">Detected Language</span>
                                            <span className="font-medium text-text-primary block uppercase">{simulationResult.language || 'en'}</span>
                                        </div>
                                    </div>

                                    {simulationResult.variables && Object.keys(simulationResult.variables).length > 0 && (
                                        <div className="space-y-1">
                                            <span className="text-xs font-semibold text-text-secondary block">Session Variables</span>
                                            <pre className="bg-slate-950 text-slate-300 p-2.5 rounded text-[10px] font-mono overflow-x-auto">
                                                {JSON.stringify(simulationResult.variables, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            )}

                            {!simulationResult && !simulatingLoading && (
                                <div className="border border-yellow-200/50 bg-yellow-50/30 p-3 rounded-lg text-xs text-yellow-700 flex items-start gap-2">
                                    <AlertTriangle size={16} className="shrink-0 mt-0.5" />
                                    <span>
                                        Note: Simulation requires an existing lead conversation matching the bot triggers. Ensure the bot trigger settings or default trigger is active.
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
};

export default FlowDesigner;
