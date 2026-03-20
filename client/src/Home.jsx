import React from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

function Home() {
  const navigate = useNavigate();

  return (
    <div className="page-container">
      <div className="card">
        <h1 className="title">결제의 정답</h1>
        <p className="subtitle">
          당신의 지갑을 지키고<br />
          가장 스마트한 혜택을 찾아드립니다.
        </p>
        <button className="btn-primary" onClick={() => navigate('/map')}>
          내 주변 혜택 지도 보기
        </button>
      </div>
    </div>
  );
}

export default Home;