import axiosInstance from '../../shared/services/axiosInstance';

export const doubletickAPI = {
    getMetrics: () => axiosInstance.get('/doubletick/metrics/'),

    getAreas: (params) => axiosInstance.get('/doubletick/areas/', { params }),
    createArea: (data) => axiosInstance.post('/doubletick/areas/', data),
    updateArea: (id, data) => axiosInstance.patch(`/doubletick/areas/${id}/`, data),
    deleteArea: (id) => axiosInstance.delete(`/doubletick/areas/${id}/`),

    getAreaAliases: (params) => axiosInstance.get('/doubletick/area-aliases/', { params }),
    createAreaAlias: (data) => axiosInstance.post('/doubletick/area-aliases/', data),
    updateAreaAlias: (id, data) => axiosInstance.patch(`/doubletick/area-aliases/${id}/`, data),
    deleteAreaAlias: (id) => axiosInstance.delete(`/doubletick/area-aliases/${id}/`),

    getAreaBranches: (params) => axiosInstance.get('/doubletick/area-branches/', { params }),
    createAreaBranch: (data) => axiosInstance.post('/doubletick/area-branches/', data),
    updateAreaBranch: (id, data) => axiosInstance.patch(`/doubletick/area-branches/${id}/`, data),
    deleteAreaBranch: (id) => axiosInstance.delete(`/doubletick/area-branches/${id}/`),

    getConversations: (params) => axiosInstance.get('/doubletick/conversations/', { params }),
    getConversation: (id) => axiosInstance.get(`/doubletick/conversations/${id}/`),
    getConversationMessages: (id) => axiosInstance.get(`/doubletick/conversations/${id}/messages/`),
    getConversationActivities: (id) => axiosInstance.get(`/doubletick/conversations/${id}/activities/`),
    syncConversationChat: (id) => axiosInstance.post(`/doubletick/conversations/${id}/sync-chat/`),
    replyToConversation: (id, data) => axiosInstance.post(`/doubletick/conversations/${id}/reply/`, data),
    requestLocation: (id) => axiosInstance.post(`/doubletick/conversations/${id}/request-location/`),
    matchArea: (id, data) => axiosInstance.post(`/doubletick/conversations/${id}/match-area/`, data),
    qualifyConversation: (id) => axiosInstance.post(`/doubletick/conversations/${id}/qualify/`),
    assignSupport: (id, data) => axiosInstance.post(`/doubletick/conversations/${id}/assign-support/`, data),
    markSpam: (id) => axiosInstance.post(`/doubletick/conversations/${id}/mark-spam/`),
    closeConversation: (id) => axiosInstance.post(`/doubletick/conversations/${id}/close/`),

    getLeads: (params) => axiosInstance.get('/doubletick/leads/', { params }),
    getLead: (id) => axiosInstance.get(`/doubletick/leads/${id}/`),
    getLeadMessages: (id) => axiosInstance.get(`/doubletick/leads/${id}/messages/`),
    getLeadActivities: (id) => axiosInstance.get(`/doubletick/leads/${id}/activities/`),
    getLeadAssignments: (id) => axiosInstance.get(`/doubletick/leads/${id}/assignments/`),
    distributeLead: (id) => axiosInstance.post(`/doubletick/leads/${id}/distribute/`),
    assignLead: (id, data) => axiosInstance.post(`/doubletick/leads/${id}/assign/`, data),
    reassignLead: (id, data) => axiosInstance.post(`/doubletick/leads/${id}/reassign/`, data),
    releaseLead: (id, data) => axiosInstance.post(`/doubletick/leads/${id}/release/`, data),
    closeLead: (id, data) => axiosInstance.post(`/doubletick/leads/${id}/close/`, data),
    addLeadActivity: (id, data) => axiosInstance.post(`/doubletick/leads/${id}/activity/`, data),

    getMobileAvailable: (params) => axiosInstance.get('/doubletick/mobile/leads/available/', { params }),
    getMobileMine: (params) => axiosInstance.get('/doubletick/mobile/leads/mine/', { params }),
    claimLead: (id) => axiosInstance.post(`/doubletick/mobile/leads/${id}/claim/`),
    openLead: (id, data) => axiosInstance.post(`/doubletick/mobile/leads/${id}/open/`, data),
    startContact: (id, data) => axiosInstance.post(`/doubletick/mobile/leads/${id}/start-contact/`, data),
    updateLeadStatus: (id, data) => axiosInstance.post(`/doubletick/mobile/leads/${id}/status/`, data),
    followUpLead: (id, data) => axiosInstance.post(`/doubletick/mobile/leads/${id}/follow-up/`, data),
    releaseMobileLead: (id, data) => axiosInstance.post(`/doubletick/mobile/leads/${id}/release/`, data),
};
