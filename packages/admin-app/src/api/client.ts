import axios from 'axios';

const client = axios.create({ baseURL: '/api', timeout: 15000 });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('adminToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  },
);

export default client;
