import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './App.css';

function BenefitPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const place = location.state?.place;

  return (
    <div className="page-container">
      <div className="card">
        <h2 className="title" style={{ color: 'var(--primary-color)' }}>💳 혜택 분석 완료!</h2>
        {place ? (
          <p className="subtitle">선택하신 <strong>{place.place_name}</strong> 매장에 대한 카드 혜택 정보를 여기에 표시할 예정입니다.</p>
        ) : (
          <p className="subtitle">장소 정보가 전달되지 않았습니다.</p>
        )}
        <button className="btn-primary" onClick={() => navigate('/map')} style={{ marginTop: '20px' }}>지도로 돌아가기</button>
      </div>
    </div>
  );
}

export default BenefitPage;