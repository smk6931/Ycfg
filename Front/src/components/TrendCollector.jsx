import React, { useState, useEffect } from 'react';
import { trendApi } from '../api/trend';

const TrendCollector = () => {
  const [country, setCountry] = useState('KR');
  const [loading, setLoading] = useState(false);
  const [contents, setContents] = useState({ youtube: [], news: [] });
  const [error, setError] = useState('');

  const countries = [
    { code: 'KR', name: '대한민국' },
    { code: 'US', name: '미국' },
    { code: 'JP', name: '일본' },
    { code: 'TW', name: '대만' },
    { code: 'ID', name: '인도네시아' }
  ];

  // 초기 로딩 및 국가 변경 시
  useEffect(() => {
    setKeywords([]); // 국가 변경 시 분석 결과 초기화
    setTranslateMode(false); // 번역 모드도 초기화
    fetchContents();
  }, [country]);

  const fetchContents = async () => {
    try {
      const res = await trendApi.getTrendingContents(country, 50);
      if (res && res.youtube) {
        setContents(res);
      }
    } catch (err) {
      console.error('조회 실패', err);
    }
  };

  const handleCollect = async () => {
    setLoading(true);
    setError('');
    setContents({ youtube: [], news: [] });
    setKeywords([]); // 분석 결과 초기화
    setTranslateMode(false); // 번역 모드 초기화

    try {
      const res = await trendApi.collectTrending(country);
      // 백엔드가 { youtube: [], news: [] } 형태를 반환함
      if (res && res.youtube) {
        setContents(res);
      } else {
        setError('데이터 형식이 올바르지 않습니다.');
      }
    } catch (err) {
      setError('수집 실패');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const [filter, setFilter] = useState('All'); // 필터 상태 추가

  // ... (중략)

  /* AI 분석 관련 State & Handler */
  const [analyzing, setAnalyzing] = useState(false);
  const [keywords, setKeywords] = useState([]);
  const [translateMode, setTranslateMode] = useState(false); // 번역 모드 상태

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      // AI 분석 API 호출 (top_n=6 정도로 카드 UI에 알맞게)
      const res = await trendApi.getTrendingKeywords(country, 6);
      if (res && res.keywords) {
        setKeywords(res.keywords);
      }
    } catch (err) {
      console.error("분석 실패", err);
      alert("AI 분석 중 오류가 발생했습니다.");
    } finally {
      setAnalyzing(false);
    }
  };

  const allItems = [
    ...contents.youtube.map(item => ({ ...item, type: 'video', score: Math.floor(item.views / 1000), source: 'YouTube' })),
    ...contents.news.map((item, idx) => ({ ...item, type: item.source === '실시간 검색어' ? 'keyword' : 'news', score: item.source === '실시간 검색어' ? 100 : 99 - idx }))
  ].sort((a, b) => b.score - a.score);

  // 필터링 적용
  const filteredItems = filter === 'All'
    ? allItems
    : allItems.filter(item => {
      if (filter === 'YouTube') return item.source === 'YouTube';
      if (filter === 'Google News') return item.source === 'Google News';
      if (filter === 'Keyword') return item.source === '실시간 검색어';
      return true;
    });

  return (
    <div className="glass-card" style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔥 실시간 인기 콘텐츠</h1>
        <p style={{ color: 'var(--text-muted)' }}>YouTube Trending + Google News Headlines + Realtime Keywords</p>
      </div>

      {/* 국가 선택 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '0.8rem', marginBottom: '1.5rem' }}>
        {countries.map((c) => (
          <button
            key={c.code}
            onClick={() => setCountry(c.code)}
            style={{
              padding: '0.6rem 1.2rem',
              borderRadius: '20px',
              border: `1px solid ${country === c.code ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}`,
              background: country === c.code ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
              color: country === c.code ? 'white' : 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: country === c.code ? 'bold' : 'normal'
            }}
          >
            {c.name}
          </button>
        ))}
      </div>

      {/* 소스 필터 탭 */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
        {['All', 'YouTube', 'Google News', ...(country === 'KR' ? ['Keyword'] : [])].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              background: 'transparent',
              border: 'none',
              color: filter === f ? 'var(--primary)' : 'var(--text-muted)',
              fontWeight: filter === f ? 'bold' : 'normal',
              cursor: 'pointer',
              fontSize: '1rem',
              padding: '0.5rem 1rem',
              borderBottom: filter === f ? '2px solid var(--primary)' : '2px solid transparent'
            }}
          >
            {f === 'Keyword' ? '실시간 검색어' : f}
          </button>
        ))}
      </div>

      {/* 수집 버튼 */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <button
          onClick={handleCollect}
          disabled={loading}
          className="btn-primary"
          style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}
        >
          {loading ? <span className="loader"></span> : `🎬 ${countries.find(c => c.code === country)?.name} 인기 콘텐츠 수집`}
        </button>
        {error && <div style={{ color: '#ef4444', marginTop: '1rem' }}>{error}</div>}
      </div>

      {/* AI 트렌드 분석 리포트 섹션 */}
      {filteredItems.length > 0 && (
        <div style={{ marginBottom: '2rem', padding: '1.5rem', background: 'rgba(139, 92, 246, 0.05)', borderRadius: '16px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: keywords.length > 0 ? '1rem' : 0 }}>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              🤖 AI 트렌드 분석 리포트
              {analyzing && <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: 'normal' }}> (분석 중...)</span>}
            </h3>

            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {keywords.length > 0 && (
                <button
                  onClick={() => setTranslateMode(!translateMode)}
                  style={{
                    background: translateMode ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
                    border: 'none',
                    padding: '0.4rem 0.8rem',
                    borderRadius: '8px',
                    color: translateMode ? 'white' : 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    marginRight: '0.5rem'
                  }}
                >
                  🌐 {translateMode ? '한국어 번역 ON' : '원문 보기'}
                </button>
              )}

              {keywords.length === 0 && (
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  style={{
                    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                    border: 'none',
                    padding: '0.6rem 1.2rem',
                    borderRadius: '20px',
                    color: 'white',
                    fontWeight: 'bold',
                    cursor: analyzing ? 'not-allowed' : 'pointer',
                    opacity: analyzing ? 0.7 : 1,
                    boxShadow: '0 4px 15px rgba(168, 85, 247, 0.4)'
                  }}
                >
                  {analyzing ? '분석 중...' : '✨ 지금 분석하기'}
                </button>
              )}

              {keywords.length > 0 && (
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  style={{
                    background: 'rgba(255,255,255,0.1)',
                    border: 'none',
                    padding: '0.4rem 0.8rem',
                    borderRadius: '8px',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.85rem'
                  }}
                >
                  🔄 다시 분석
                </button>
              )}
            </div>
          </div>

          {/* 분석 결과 (키워드 카드) */}
          {keywords.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
              {keywords.map((k, idx) => (
                <div key={idx} className="glass-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 'bold', color: 'var(--primary)', fontSize: '1.1rem' }}>#{idx + 1}</span>
                    <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', padding: '0.2rem 0.6rem', borderRadius: '10px' }}>
                      언급 {k.count}회
                    </span>
                  </div>
                  <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', fontSize: '1.05rem', minHeight: '1.5em' }}>
                    {translateMode ? (k.keyword_kr || k.keyword) : k.keyword}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                    {k.reason}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 콘텐츠 리스트 (Table View) */}
      <div style={{ overflowX: 'auto' }}>
        {filteredItems.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(255,255,255,0.1)' }}>
                <th style={{ padding: '1rem', textAlign: 'left', width: '50px' }}>Rank</th>
                <th style={{ padding: '1rem', textAlign: 'left' }}>제목</th>
                <th style={{ padding: '1rem', textAlign: 'center', width: '100px' }}>출처</th>
                <th style={{ padding: '1rem', textAlign: 'center', width: '100px' }}>조회수/점수</th>
                <th style={{ padding: '1rem', textAlign: 'center', width: '80px' }}>타입</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}
                  onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}>
                  <td style={{ padding: '1rem', fontWeight: 'bold', color: idx < 3 ? 'var(--primary)' : 'inherit' }}>
                    #{idx + 1}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <a href={item.url} target="_blank" rel="noreferrer" style={{ color: 'white', textDecoration: 'none', fontWeight: '500' }}>
                      {item.title}
                    </a>
                    {item.type === 'video' && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>{item.channel}</div>}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                    {item.type === 'video' ? 'YouTube' : item.source || 'News'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center', fontWeight: 'bold', color: 'var(--primary)' }}>
                    {item.type === 'video' ? `${(item.views / 1000).toFixed(0)}K` : item.score}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'center' }}>
                    <span style={{ padding: '0.3rem 0.8rem', borderRadius: '12px', background: item.type === 'video' ? 'rgba(255,0,0,0.2)' : 'rgba(0,150,255,0.2)', fontSize: '0.8rem' }}>
                      {item.type === 'video' ? '📺' : '📰'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            데이터가 없습니다. 수집 버튼을 눌러주세요.
          </div>
        )}
      </div>
    </div>
  );
};

export default TrendCollector;
