import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
import { startBackendWarmup } from './utils/warmBackend.js';

startBackendWarmup();

// Developer Console Security & Self-XSS Warning (Facebook / Discord format)
if (typeof window !== 'undefined') {
  const titleStyle = 'color: #ef4444; font-size: 58px; font-weight: 900; -webkit-text-stroke: 1.5px black; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
  const textStyle = 'color: #f1f5f9; font-size: 15px; font-weight: 600; line-height: 1.6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
  const linkStyle = 'color: #38bdf8; font-size: 15px; font-weight: 700; text-decoration: underline; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';

  console.log('%cStop!', titleStyle);
  console.log(
    `%cThis is a browser feature intended for developers. If someone told you to copy and paste something here to enable an OVD Downloader feature, download private media, or "hack" someone's account, it is a scam and will give them unauthorized access to your computer and accounts.\n\n%cSee https://ovd.winplaybox.in/security for more information.`,
    textStyle,
    linkStyle
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
