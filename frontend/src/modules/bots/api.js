import axiosInstance from '../../shared/services/axiosInstance';

export const botsAPI = {
    getStats: () => axiosInstance.get('/bots/bots/stats/'),

    getBots: (params) => axiosInstance.get('/bots/bots/', { params }),
    getBot: (id) => axiosInstance.get(`/bots/bots/${id}/`),
    createBot: (data) => axiosInstance.post('/bots/bots/', data),
    updateBot: (id, data) => axiosInstance.patch(`/bots/bots/${id}/`, data),
    deleteBot: (id) => axiosInstance.delete(`/bots/bots/${id}/`),
    cloneBot: (id, data) => axiosInstance.post(`/bots/bots/${id}/clone/`, data),

    getFlows: (params) => axiosInstance.get('/bots/flows/', { params }),
    createFlow: (data) => axiosInstance.post('/bots/flows/', data),
    updateFlow: (id, data) => axiosInstance.patch(`/bots/flows/${id}/`, data),
    publishFlow: (id) => axiosInstance.post(`/bots/flows/${id}/publish/`),

    getNodes: (params) => axiosInstance.get('/bots/nodes/', { params }),
    createNode: (data) => axiosInstance.post('/bots/nodes/', data),
    updateNode: (id, data) => axiosInstance.patch(`/bots/nodes/${id}/`, data),
    deleteNode: (id) => axiosInstance.delete(`/bots/nodes/${id}/`),
    testNode: (id, data) => axiosInstance.post(`/bots/nodes/${id}/test/`, data),

    getNodeOptions: (params) => axiosInstance.get('/bots/node-options/', { params }),
    createNodeOption: (data) => axiosInstance.post('/bots/node-options/', data),
    updateNodeOption: (id, data) => axiosInstance.patch(`/bots/node-options/${id}/`, data),
    deleteNodeOption: (id) => axiosInstance.delete(`/bots/node-options/${id}/`),

    getTransitions: (params) => axiosInstance.get('/bots/transitions/', { params }),
    createTransition: (data) => axiosInstance.post('/bots/transitions/', data),
    updateTransition: (id, data) => axiosInstance.patch(`/bots/transitions/${id}/`, data),
    deleteTransition: (id) => axiosInstance.delete(`/bots/transitions/${id}/`),

    getTriggers: (params) => axiosInstance.get('/bots/triggers/', { params }),
    createTrigger: (data) => axiosInstance.post('/bots/triggers/', data),
    updateTrigger: (id, data) => axiosInstance.patch(`/bots/triggers/${id}/`, data),
    deleteTrigger: (id) => axiosInstance.delete(`/bots/triggers/${id}/`),

    getSessions: (params) => axiosInstance.get('/bots/sessions/', { params }),
    getSessionVariables: (params) => axiosInstance.get('/bots/session-variables/', { params }),
    getExecutionLogs: (params) => axiosInstance.get('/bots/execution-logs/', { params }),
    testFlow: (data) => axiosInstance.post('/bots/test-flow/', data),

    getMessageTemplates: (params) => axiosInstance.get('/bots/message-templates/', { params }),
    createMessageTemplate: (data) => axiosInstance.post('/bots/message-templates/', data),
    updateMessageTemplate: (id, data) => axiosInstance.patch(`/bots/message-templates/${id}/`, data),
    deleteMessageTemplate: (id) => axiosInstance.delete(`/bots/message-templates/${id}/`),

    getIntegrations: (params) => axiosInstance.get('/bots/integrations/', { params }),
    createIntegration: (data) => axiosInstance.post('/bots/integrations/', data),
    updateIntegration: (id, data) => axiosInstance.patch(`/bots/integrations/${id}/`, data),
    deleteIntegration: (id) => axiosInstance.delete(`/bots/integrations/${id}/`),

    getDataSources: (params) => axiosInstance.get('/bots/data-sources/', { params }),
    createDataSource: (data) => axiosInstance.post('/bots/data-sources/', data),
    updateDataSource: (id, data) => axiosInstance.patch(`/bots/data-sources/${id}/`, data),
    deleteDataSource: (id) => axiosInstance.delete(`/bots/data-sources/${id}/`),

    getFallbackRules: (params) => axiosInstance.get('/bots/fallback-rules/', { params }),
    createFallbackRule: (data) => axiosInstance.post('/bots/fallback-rules/', data),
    updateFallbackRule: (id, data) => axiosInstance.patch(`/bots/fallback-rules/${id}/`, data),
    deleteFallbackRule: (id) => axiosInstance.delete(`/bots/fallback-rules/${id}/`),

    getHandoverRules: (params) => axiosInstance.get('/bots/handover-rules/', { params }),
    createHandoverRule: (data) => axiosInstance.post('/bots/handover-rules/', data),
    updateHandoverRule: (id, data) => axiosInstance.patch(`/bots/handover-rules/${id}/`, data),
    deleteHandoverRule: (id) => axiosInstance.delete(`/bots/handover-rules/${id}/`),

    getApiCallLogs: (params) => axiosInstance.get('/bots/api-call-logs/', { params }),
    getSheetSyncLogs: (params) => axiosInstance.get('/bots/sheet-sync-logs/', { params }),
};
