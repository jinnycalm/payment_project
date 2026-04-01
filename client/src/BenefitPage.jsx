import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import './App.css';

function BenefitPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // location.state가 없으면 지도 페이지로 리디렉션
  useEffect(() => {
    if (!location.state) {
      navigate('/');
    }
  }, [location, navigate]);

  if (!location.state) {
    return null; // 리디렉션 중에는 아무것도 렌더링하지 않음
  }

  const { place, analysisResult } = location.state;
  const briefingText = analysisResult.data; 

  return (
    <div className="page-container">
      <div className="card">
        {briefingText ? (
          // ReactMarkdown 컴포넌트를 사용하여 마크다운 텍스트 렌더링
          <div className="markdown-content">
            <ReactMarkdown>{briefingText}</ReactMarkdown>
          </div>
        ) : (
          <div className="no-benefit-info">
            <h1 className="title" style={{fontSize: '24px'}}>✨ <span className="highlight">{place.place_name}</span> 혜택 분석 ✨</h1>
            <p className="subtitle" style={{fontSize: '16px'}}>😭 현재 적용 가능한 카드 혜택을 찾지 못했습니다.</p>
          </div>
        )}

        <button onClick={() => navigate('/map')} className="btn-primary" style={{marginTop: '24px'}}>
          지도로 돌아가기
        </button>
      </div>
    </div>
  );
}

export default BenefitPage;
