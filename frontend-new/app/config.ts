// API configuration that works both locally and on server
const getApiUrl = () => {
  // If we're in the browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If accessing via server IP or domain, use that
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `http://${hostname}:8001`;
    }
  }
  
  // Otherwise use localhost for local development
  return 'http://localhost:8001';
};

export const API_URL = getApiUrl();
