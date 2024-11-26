import axios from 'axios'
export const client = axios.create({
    baseURL: import.meta.env.VA_BACKEND_URL || "pods-tacc-icicleai-vadashback",
    // timeout: 1000,
});
