import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("kn_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (data) => api.post("/api/auth/register", data),
  login: (data) => api.post("/api/auth/login", data),
};

export const courseAPI = {
  getAll: () => api.get("/api/courses"),
  create: (data) => api.post("/api/courses", data),
  enroll: (courseId) => api.post(`/api/courses/${courseId}/enroll`, {}),
  unenroll: (courseId) =>
    api.delete(`/api/courses/${courseId}/enroll`, {
      data: {},
      headers: {
        "Content-Type": "application/json",
      },
    }),
  getEnrollments: () => api.get("/api/enrollments"),
};

export const reviewAPI = {
  create: (courseId, data) =>
    api.post(`/api/courses/${courseId}/reviews`, data),
  getByCourse: (courseId) => api.get(`/api/courses/${courseId}/reviews`),
};

export default api;
