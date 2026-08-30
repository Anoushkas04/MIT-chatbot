import React from 'react';
import { renderToString } from 'react-dom/server';
import App from './src/App.jsx';

try {
  console.log("Attempting to render <App /> component...");
  const html = renderToString(React.createElement(App));
  console.log("SUCCESS! <App /> rendered HTML length:", html.length);
  console.log("HTML Preview (first 200 chars):", html.slice(0, 200));
} catch (err) {
  console.error("❌ CRITICAL REACT RENDER ERROR:", err);
}
