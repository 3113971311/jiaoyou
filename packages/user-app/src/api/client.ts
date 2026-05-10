import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

// 请求拦截：自动附加 access token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：401 时尝试刷新 token
let isRefreshing = false;
let refreshQueue: Array<{ resolve: (v: any) => void; reject: (e: any) => void }> = [];

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { config, response } = error;
    if (response?.status === 401 && !config._retry && !config.url?.includes('/auth/refresh')) {
      config._retry = true;
      if (!isRefreshing) {
        isRefreshing = true;
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          localStorage.clear();
          window.location.href = '/login';
          return Promise.reject(error);
        }
        try {
          const res = await axios.post('/api/auth/refresh', { refreshToken });
          const { accessToken, refreshToken: newRefresh } = res.data;
          localStorage.setItem('accessToken', accessToken);
          localStorage.setItem('refreshToken', newRefresh);
          refreshQueue.forEach((p) => p.resolve(accessToken));
          refreshQueue = [];
          config.headers.Authorization = `Bearer ${accessToken}`;
          return client(config);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
          return Promise.reject(error);
        } finally {
          isRefreshing = false;
        }
      } else {
        return new Promise((resolve, reject) => {
          refreshQueue.push({
            resolve: (token: string) => {
              config.headers.Authorization = `Bearer ${token}`;
              resolve(client(config));
            },
            reject,
          });
        });
      }
    }
    return Promise.reject(error);
  },
);

export default client;
