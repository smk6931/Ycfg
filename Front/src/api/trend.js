import apiClient from './client';

export const trendApi = {
  // 실시간 인기 콘텐츠 수집 (YouTube + News)
  collectTrending: async (country = 'KR') => {
    const response = await apiClient.post(`/trend/collect-trending?country=${country}`);
    return response.data;
  },

  // 수집된 인기 콘텐츠 조회
  getTrendingContents: async (country = 'KR', limit = 50) => {
    const response = await apiClient.get('/trend/trending/contents', {
      params: { country, limit }
    });
    return response.data;
  },

  // 트렌드 키워드 분석 (AI)
  getTrendingKeywords: async (country = 'KR', top_n = 10) => {
    const response = await apiClient.get('/trend/trending/keywords', {
      params: { country, top_n }
    });
    return response.data;
  }
};
