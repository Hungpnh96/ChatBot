import React from 'react';
import ChatUI from './ChatUI.tsx';
import HealthDashboard from './components/HealthDashboard.tsx';

function App() {
  // Check if we're on the health dashboard route
  if (window.location.pathname === '/health') {
    return <HealthDashboard />;
  }

  return (
    <div className="App">
      <ChatUI />
    </div>
  );
}

export default App;