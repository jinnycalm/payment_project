import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

// 카카오에서 제공하는 카테고리
const CATEGORIES = [
    { id: 'FD6', name: '음식점', color: '#ff6699' },
    { id: 'CE7', name: '카페', color: '#8d6e63' },
    { id: 'CS2', name: '편의점', color: '#ff9e0f' },
    { id: 'HP8', name: '병원', color: '#e57373' },
    { id: 'PM9', name: '약국', color: '#4db6ac' },
    { id: 'MT1', name: '대형마트', color: '#f55354' },
    { id: 'AC5', name: '학원', color: '#99cc00' },
    { id: 'PK6', name: '주차장', color: '#0099cc' },
    { id: 'OL7', name: '주유소/충전소', color: '#003399' },
];

function MapPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [location, setLocation] = useState({ lat: 37.5048, lon: 127.0043 }); // 기본값(고터)
  const [activeCategory, setActiveCategory] = useState('');
  const [keyword, setKeyword] = useState('');
  const [analyzingPlace, setAnalyzingPlace] = useState(null); // 분석 중인 장소 정보

  // 카카오맵 관련 객체들을 유지하기 위한 refs
  const mapRef = useRef(null);
  const psRef = useRef(null);
  const markersRef = useRef([]);
  const overlayRef = useRef(null);
  const activeCategoryRef = useRef(activeCategory);

  useEffect(() => {
    const fetchIpAndLocation = async () => {
      try {
        // 1. 접속자 IP 가져오기
        const ipRes = await fetch('https://api.ipify.org?format=json');
        const ipData = await ipRes.json();        

        // 2. IP 기반 위치 정보 가져오기
        const geoRes = await fetch(`http://ip-api.com/json/${ipData.ip}`);
        const geoData = await geoRes.json();

        if (geoData.status === 'success') {
          setLocation({ lat: geoData.lat, lon: geoData.lon });
        }
      } catch (error) {
        console.error('❌ 위치 정보를 가져오는데 실패했습니다.', error);
      } finally {
        // 화면 전환(점검중 문구 표시)을 자연스럽게 보여주기 위해 약간의 딜레이 추가
        setTimeout(() => setLoading(false), 1000);
      }
    };

    fetchIpAndLocation();
  }, []);

  useEffect(() => {
    // 로딩 완료 후 지도 초기화
    if (!loading && window.kakao && window.kakao.maps && window.kakao.maps.services) {
      const container = document.getElementById('map');
      const options = {
        center: new window.kakao.maps.LatLng(location.lat, location.lon),
        level: 3
      };
      const map = new window.kakao.maps.Map(container, options);
      mapRef.current = map;
      psRef.current = new window.kakao.maps.services.Places(map);

      // 지도 중심이 이동하거나 확대/축소될 때마다 활성화된 카테고리가 있으면 재검색
      window.kakao.maps.event.addListener(map, 'idle', () => {
        if (activeCategoryRef.current) {
          searchByCategory(activeCategoryRef.current);
        }
      });
    }
  }, [loading, location]);

  // 활성화된 카테고리가 변경될 때마다 ref 업데이트 및 장소 검색
  useEffect(() => {
    activeCategoryRef.current = activeCategory;
    if (activeCategory) {
      searchByCategory(activeCategory);
    } else {
      removeMarkers();
      if (overlayRef.current) overlayRef.current.setMap(null);
    }
  }, [activeCategory]);

  // 카테고리로 검색 (현재 지도 영역 기준)
  const searchByCategory = (categoryCode) => {
    if (!psRef.current) return;
    psRef.current.categorySearch(categoryCode, placesSearchCB, { useMapBounds: true });
  };

  // 키워드로 장소/지역 검색
  const handleKeywordSearch = (e) => {
    e.preventDefault();
    if (!keyword.trim() || !psRef.current) return;
    setActiveCategory(''); // 키워드 검색 시 카테고리 필터 초기화
    psRef.current.keywordSearch(keyword, placesSearchCB);
  };

  // 장소 검색 콜백 함수
  const placesSearchCB = (data, status) => {
    if (status === window.kakao.maps.services.Status.OK) {
      displayPlaces(data);
    } else if (status === window.kakao.maps.services.Status.ZERO_RESULT) {
      removeMarkers();
      if (overlayRef.current) overlayRef.current.setMap(null);
    } else if (status === window.kakao.maps.services.Status.ERROR) {
      alert('검색 중 오류가 발생했습니다.');
    }
  };

  // 검색된 장소들을 마커로 표시
  const displayPlaces = (places) => {
    removeMarkers();
    if (overlayRef.current) overlayRef.current.setMap(null);
    
    const bounds = new window.kakao.maps.LatLngBounds();

    places.forEach((place) => {
      const marker = addMarker(place);
      bounds.extend(new window.kakao.maps.LatLng(place.y, place.x));
    });

    // 키워드 검색의 경우에만 지도 범위를 결과에 맞게 재조정 (카테고리는 현재 화면 기준이므로 제외)
    if (!activeCategoryRef.current && places.length > 0) {
      mapRef.current.setBounds(bounds);
    }
  };

  // 커스텀 이미지 마커 생성 및 클릭 이벤트 추가
  const addMarker = (place) => {
    const cat = CATEGORIES.find(c => c.id === place.category_group_code) || { color: '#3182f6' };
    
    // 각 카테고리 색상을 입힌 SVG 데이터 URI 생성
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="40" viewBox="0 0 28 40"><path fill="${cat.color}" stroke="#ffffff" stroke-width="1.5" d="M14 0C6.268 0 0 6.268 0 14c0 10 14 26 14 26s14-16 14-26c0-7.732-6.268-14-14-14z"/><circle cx="14" cy="14" r="6" fill="#ffffff"/></svg>`;
    const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    const imageSize = new window.kakao.maps.Size(28, 40);
    const markerImage = new window.kakao.maps.MarkerImage(url, imageSize, { offset: new window.kakao.maps.Point(14, 40) });

    const marker = new window.kakao.maps.Marker({
      position: new window.kakao.maps.LatLng(place.y, place.x),
      image: markerImage
    });

    marker.setMap(mapRef.current);
    markersRef.current.push(marker);

    // 마커 클릭 시 정보 말풍선 표시
    window.kakao.maps.event.addListener(marker, 'click', () => {
      displayInfoWindow(marker, place);
    });

    return marker;
  };

  // 지도 위 마커 모두 제거
  const removeMarkers = () => {
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];
  };

  // 말풍선(CustomOverlay) 띄우기
  const displayInfoWindow = (marker, place) => {
    if (overlayRef.current) overlayRef.current.setMap(null);

    const content = document.createElement('div');
    content.className = 'place-overlay';
    content.innerHTML = `
      <div class="overlay-title">${place.place_name}</div>
      <div class="overlay-desc">${place.category_group_name || place.address_name}</div>
      <button class="btn-check-benefit">이 매장 혜택 확인하기</button>
    `;

    // 혜택 확인 버튼 클릭 이벤트 (리액트 방식이 아닌 DOM 이벤트 연결)
    content.querySelector('.btn-check-benefit').onclick = () => {
      setAnalyzingPlace(place);
      // 약 1.5초 후 혜택 확인 페이지로 이동 (카드 정보 RAG 처리를 위해)
      setTimeout(() => navigate('/benefit', { state: { place } }), 1500);
    };

    const overlay = new window.kakao.maps.CustomOverlay({
      position: marker.getPosition(),
      content: content,
      yAnchor: 1.3 // 마커 위쪽으로 말풍선 띄우기
    });

    overlay.setMap(mapRef.current);
    overlayRef.current = overlay;
  };

  return (
    <div className="page-container">
      {/* 혜택 분석 중일 때 덮어씌워지는 전체화면 로딩 UI */}
      {analyzingPlace && (
        <div className="benefit-loading-overlay">
          <h2>🔎 혜택 확인중</h2>
          <p>'{analyzingPlace.place_name}' 에서 받을 수 있는 혜택을 확인중입니다.</p>
        </div>
      )}

      <div className="map-card">
        {loading ? (
          <div className="loading-text">
            IP 주소를 바탕으로 현재 위치를 찾는 중입니다...
          </div>
        ) : (
          <>
            <div className="map-controls">
              <form className="search-form" onSubmit={handleKeywordSearch}>
                <input 
                  type="text" 
                  className="search-input" 
                  placeholder="지역이나 장소를 검색해보세요 (예: 강남역 스타벅스)" 
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
                <button type="submit" className="search-btn">검색</button>
              </form>
              <div className="category-list">
                {CATEGORIES.map(cat => (
                  <button 
                    key={cat.id} 
                    className={`category-btn ${activeCategory === cat.id ? 'active' : ''}`}
                    onClick={() => setActiveCategory(activeCategory === cat.id ? '' : cat.id)}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>
            <div id="map" className="map-container"></div>
          </>
        )}
      </div>
    </div>
  );
}

export default MapPage;