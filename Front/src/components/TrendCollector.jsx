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

  // 초기 로딩
  useEffect(() => {
    fetchContents();
  }, [country]);

  const fetchContents = async () => {
    try {
      const res = await trendApi.getTrendingContents(country, 50);
      setContents(res.data);
    } catch (err) {
      console.error('조회 실패', err);
    }
  };

  const handleCollect = async () => {
    setLoading(true);
    setError('');
    setContents({ youtube: [], news: [] });

    try {
      const res = await trendApi.collectTrending(country);
      if (res.data.success) {
        await fetchContents();
      } else {
        setError(res.data.message);
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
        {['All', 'YouTube', 'Google News', 'Keyword'].map((f) => (
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
