import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('shuleconnect_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const schoolId = localStorage.getItem('shuleconnect_school_id');
  if (schoolId) {
    config.headers['X-School-ID'] = schoolId;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('shuleconnect_token');
        localStorage.removeItem('shuleconnect_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
