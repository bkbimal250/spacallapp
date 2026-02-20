import { format } from 'date-fns';

export const formatDate = (date, formatStr = 'MMM dd, yyyy') => {
    if (!date) return '';
    return format(new Date(date), formatStr);
};
