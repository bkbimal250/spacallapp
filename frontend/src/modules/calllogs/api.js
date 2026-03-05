import axiosInstance from '../../shared/services/axiosInstance';

export const callLogsAPI = {
    getCallLogs: (params) => axiosInstance.get('/calllogs/', { params }),
    getCallLogStats: (params) => axiosInstance.get('/calllogs/stats/', { params }),
    getBranchSummary: (params) => axiosInstance.get('/calllogs/branch_summary/', { params }),
    deleteCallLog: (id) => axiosInstance.delete(`/calllogs/${id}/`),
    bulkDeleteCallLogs: (ids) => axiosInstance.post('/calllogs/bulk_delete/', { ids }),
    exportExcel: (params) => axiosInstance.get('/calllogs/export_excel/', {
        params,
        responseType: 'blob'
    }),
};
