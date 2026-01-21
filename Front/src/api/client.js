import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8001', // 백엔드 주소
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
