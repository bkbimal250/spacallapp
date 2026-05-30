import { useContext } from 'react';
import { AuthContext } from '../../../app/App';

export const useAuth = () => {
    return useContext(AuthContext);
};
