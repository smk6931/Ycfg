import apiClient from './client';

export const trendApi = {
  // 실시간 인기 콘텐츠 수집 (YouTube + News)
  collectTrending: async (country = 'KR') => {
    return await apiClient.post(`/trend/collect-trending?country=${country}`);
  },

  // 수집된 인기 콘텐츠 조회
  getTrendingContents: async (country = 'KR', limit = 50) => {
    return await apiClient.get('/trend/trending/contents', {
      params: { country, limit }
    });
  }
};
