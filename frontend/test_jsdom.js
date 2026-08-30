import fs from 'fs';
import path from 'path';
import { JSDOM, VirtualConsole } from 'jsdom';

const virtualConsole = new VirtualConsole();
const errors = [];
const logs = [];

virtualConsole.on('error', (...args) => errors.push(args.join(' ')));
virtualConsole.on('jsdomError', (err) => errors.push(err.message || String(err)));
virtualConsole.on('log', (...args) => logs.push(args.join(' ')));

const html = fs.readFileSync(path.join(process.cwd(), 'dist', 'index.html'), 'utf8');

// Find JS bundle file in dist/assets
const files = fs.readdirSync(path.join(process.cwd(), 'dist', 'assets'));
const jsFile = files.find(f => f.endsWith('.js'));
const jsCode = fs.readFileSync(path.join(process.cwd(), 'dist', 'assets', jsFile), 'utf8');

// Replace script tag with inline script for JSDOM testing
const inlinedHtml = html.replace(/<script type="module"[^>]*><\/script>/, `<script>${jsCode}</script>`);

console.log(`Evaluating ${jsFile} inline inside JSDOM...`);

const dom = new JSDOM(inlinedHtml, {
  url: 'http://localhost:5173/',
  runScripts: 'dangerously',
  virtualConsole,
});

setTimeout(() => {
  console.log("\n--- JSDOM Inline Execution Results ---");
  const rootHtml = dom.window.document.getElementById('root')?.innerHTML || "";
  console.log("Root element rendered HTML length:", rootHtml.length);
  console.log("Root HTML preview (first 250 chars):", rootHtml.slice(0, 250));
  if (errors.length > 0) {
    console.error("❌ BROWSER CONSOLE ERRORS CAPTURED:", errors);
  } else {
    console.log("✓ No browser runtime errors during mount.");
  }
  process.exit(0);
}, 2000);
