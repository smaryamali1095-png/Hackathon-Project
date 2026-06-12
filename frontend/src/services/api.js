import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const analyzeRisk = (cnic) => api.get(`/data/analyze-risk/${cnic}`);
export const uploadData = (type, formData) => api.post(`/data/upload/${type}`, formData);