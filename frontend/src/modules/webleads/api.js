import axiosInstance from '../../shared/services/axiosInstance';

const base = '/web-leads';

export const getWebsiteForms = (params) => axiosInstance.get(`${base}/configurations/`, { params });
export const createWebsiteForm = (payload) => axiosInstance.post(`${base}/configurations/`, payload);
export const getWebsiteForm = (id) => axiosInstance.get(`${base}/configurations/${id}/`);
export const updateWebsiteForm = (id, payload) => axiosInstance.patch(`${base}/configurations/${id}/`, payload);
export const deleteWebsiteForm = (id) => axiosInstance.delete(`${base}/configurations/${id}/`);

export const getWebsiteLeads = (params) => axiosInstance.get(`${base}/leads/`, { params });
export const getWebsiteLead = (id) => axiosInstance.get(`${base}/leads/${id}/`);
export const updateWebsiteLead = (id, payload) => axiosInstance.patch(`${base}/leads/${id}/`, payload);
export const assignWebsiteLead = (id, payload) => axiosInstance.post(`${base}/leads/${id}/assign/`, payload);

export const getWebLeadOverviewAnalytics = (params) => axiosInstance.get(`${base}/analytics/overview/`, { params });
export const getWebLeadBranchAnalytics = (params) => axiosInstance.get(`${base}/analytics/branches/`, { params });
export const getWebLeadWebsiteAnalytics = (params) => axiosInstance.get(`${base}/analytics/websites/`, { params });
export const getWebLeadFormAnalytics = (params) => axiosInstance.get(`${base}/analytics/forms/`, { params });

export const getPublicFormConfig = (formKey) => axiosInstance.get(`${base}/config/${formKey}/`);

export const webLeadsAPI = {
    getWebsiteForms,
    createWebsiteForm,
    getWebsiteForm,
    updateWebsiteForm,
    deleteWebsiteForm,
    getWebsiteLeads,
    getWebsiteLead,
    updateWebsiteLead,
    assignWebsiteLead,
    getWebLeadOverviewAnalytics,
    getWebLeadBranchAnalytics,
    getWebLeadWebsiteAnalytics,
    getWebLeadFormAnalytics,
    getPublicFormConfig,
};
