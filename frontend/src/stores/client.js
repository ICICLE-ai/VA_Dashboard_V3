import axios from 'axios'
export const client = axios.create({
    baseURL: import.meta.env.VA_BACKEND_URL || "__BACKEND_BASE_URL__",
    // timeout: 1000,
});
