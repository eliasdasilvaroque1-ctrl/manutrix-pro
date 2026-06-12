import axios from "axios";
import { createContext, useContext } from "react";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
export const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// API Client
export const api = axios.create({ baseURL: API });
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('manutrix_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('manutrix_token');
      sessionStorage.removeItem('manutrix_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
