import React, { useEffect, useState } from 'react';

import RiderPage from './App.jsx';
import ModeNav from './components/ModeNav.jsx';
import AdminPage from './pages/AdminPage.jsx';
import DriverPage from './pages/DriverPage.jsx';

const getRouteKey = (pathname) => {
  if (pathname === '/admin') return 'admin';
  if (pathname === '/driver') return 'driver';
  return 'rider';
};

const RootApp = () => {
  const [route, setRoute] = useState(() => getRouteKey(window.location.pathname));

  useEffect(() => {
    const handlePopState = () => setRoute(getRouteKey(window.location.pathname));
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleNavigate = (path) => {
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
      setRoute(getRouteKey(path));
    }
  };

  return (
    <>
      <ModeNav currentRoute={route} onNavigate={handleNavigate} />
      {route === 'admin' ? <AdminPage /> : route === 'driver' ? <DriverPage /> : <RiderPage />}
    </>
  );
};

export default RootApp;
