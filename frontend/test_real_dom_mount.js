import { JSDOM } from 'jsdom';
import React from 'react';
import { createRoot } from 'react-dom/client';

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://localhost:5173/',
});

global.window = dom.window;
global.document = dom.window.document;

Object.defineProperty(global, 'navigator', {
  value: dom.window.navigator,
  writable: true,
  configurable: true,
});

global.window.fetch = async (url) => {
  console.log("JSDOM fetch called for:", url);
  return {
    ok: true,
    json: async () => ([]),
  };
};

import App from './src/App.jsx';

console.log("Attempting to mount React <App /> into JSDOM #root element...");

try {
  const container = document.getElementById('root');
  const root = createRoot(container);
  root.render(React.createElement(App));

  setTimeout(() => {
    console.log("\n--- REAL REACT DOM MOUNT RESULT ---");
    const renderedHtml = container.innerHTML;
    console.log("Rendered HTML length:", renderedHtml.length);
    console.log("Rendered HTML snippet (first 300 chars):", renderedHtml.slice(0, 300));
    if (renderedHtml.length > 500) {
      console.log("✅ SUCCESS! React mounted the application DOM elements into #root cleanly!");
    } else {
      console.error("⚠️ WARNING: #root innerHTML is empty or suspiciously short!");
    }
    process.exit(0);
  }, 1000);
} catch (err) {
  console.error("❌ CRITICAL MOUNT CRASH DETECTED:", err);
  process.exit(1);
}
