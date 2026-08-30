import fs from 'fs';
import path from 'path';
import { createServer } from 'vite';

async function runTest() {
  const server = await createServer({
    server: { middlewareMode: true },
    appType: 'custom',
  });

  const srcDir = path.join(process.cwd(), 'src');

  async function checkFile(filePath) {
    try {
      await server.transformRequest(filePath);
    } catch (err) {
      console.error(`❌ TRANSFORM ERROR IN FILE: ${filePath}`);
      console.error(err);
    }
  }

  function checkDir(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        checkDir(fullPath);
      } else if (entry.name.endsWith('.jsx') || entry.name.endsWith('.js')) {
        const relativePath = '/' + path.relative(process.cwd(), fullPath);
        checkFile(relativePath);
      }
    }
  }

  console.log("Checking all files in src/ using Vite transformer...");
  checkDir(srcDir);
  setTimeout(async () => {
    await server.close();
    console.log("Vite transform check complete.");
    process.exit(0);
  }, 1000);
}

runTest();
