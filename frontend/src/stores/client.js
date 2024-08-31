import axios from 'axios'
export const client = axios.create({
    baseURL: import.meta.env.VITE_APP_BACKEND_BASE_URL || "__BACKEND_BASE_URL__",
    // timeout: 1000,
});
