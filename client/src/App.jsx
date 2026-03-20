import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Home';
import MapPage from './MapPage';
import BenefitPage from './BenefitPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/benefit" element={<BenefitPage />} />
      </Routes>
    </Router>
  );
}

export default App;
