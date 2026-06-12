import axios from "axios";

export const API_BASE = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
});

// Attach admin token with every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("tax_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Handle expired/invalid token safely
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const currentPath = window.location.pathname;

    if (error.response?.status === 401) {
      localStorage.removeItem("tax_token");
      localStorage.removeItem("isAuthenticated");
      localStorage.removeItem("user");
      localStorage.removeItem("role");

      if (currentPath !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

// =====================
// AUTH
// =====================
export const login = (username, password) =>
  api.post("/auth/login", { username, password });

export const registerAdmin = (username, password) =>
  api.post("/auth/register-admin", { username, password });

// =====================
// DASHBOARD / SUMMARY
// =====================
export const summaryStats = () =>
  api.get("/data/summary-stats");

export const status = () =>
  api.get("/data/status");

export const regionalCompliance = () =>
  api.get("/data/regional-compliance");

// =====================
// RISK ANALYSIS
// =====================
export const analyzeRisk = (cnic) =>
  api.get(`/data/analyze-risk/${cnic}`);

export const riskRanking = () =>
  api.get("/data/risk-ranking");

export const graphAiAnomalies = () =>
  api.get("/data/graph-ai/anomalies");

// =====================
// SEARCH / GRAPH
// =====================
export const searchEntity = (q) =>
  api.get("/data/search", { params: { q } });

export const graphByCnic = (cnic) =>
  api.get(`/data/graph/${cnic}`);

// =====================
// REPORTS
// =====================
export const reportUrl = (cnic) =>
  `${API_BASE}/data/download-report/${cnic}`;

// =====================
// DATA UPLOAD
// =====================
export const uploadData = (type, formData) =>
  api.post(`/data/upload/${type}`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
export const entityResolution = (threshold = 75) =>
  api.get("/data/entity-resolution", { params: { threshold } });

export const gnnAnomalies = () =>
  api.get("/data/gnn-anomalies");

export const auditTrail = (cnic) =>
  api.get(`/data/audit-trail/${cnic}`);
export const searchCitizens = (q = "") =>
  api.get("/data/citizens/search", { params: { q } });

export const knowledgeGraphByCnic = (cnic, fiscalYear = "") =>
  api.get(`/data/knowledge-graph/${cnic}`, {
    params: fiscalYear ? { fiscal_year: fiscalYear } : {}
  });
export const declarationGap = (cnic, fiscalYear = "2026") =>
  api.get(`/data/declaration-gap/${cnic}`, {
    params: { fiscal_year: fiscalYear }
  });
export const uploadDataset = (datasetType, fiscalYear, file) => {
  const formData = new FormData();
  formData.append("fiscal_year", fiscalYear);
  formData.append("file", file);

  return uploadData(datasetType, formData);
};

export default api;