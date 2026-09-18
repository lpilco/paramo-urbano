/**
 * @fileoverview High-performance, robust server for Páramo Urbano frontend.
 * Serves pre-compiled production assets with client-side SPA routing
 * and reverse proxies `/api/*` to the FastAPI backend on port 8000.
 */

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.join(__dirname, 'dist');
const port = 3000;
const host = '0.0.0.0';

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};

const server = http.createServer((req, res) => {
  const urlPath = req.url || '/';

  // Reverse proxy for backend API calls
  if (urlPath.startsWith('/api/')) {
    const backendHeaders = { ...req.headers };
    delete backendHeaders.host;

    const proxyReq = http.request(
      `http://127.0.0.1:8000${urlPath}`,
      {
        method: req.method,
        headers: backendHeaders,
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
        proxyRes.pipe(res);
      }
    );

    proxyReq.on('error', (err) => {
      res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(
        JSON.stringify({
          title: 'Backend Unreachable',
          status: 502,
          detail: `Could not proxy request to backend: ${err.message}`,
        })
      );
    });

    req.pipe(proxyReq);
    return;
  }

  // Static file serving with SPA fallback
  const cleanPath = urlPath.split('?')[0];
  let targetFile = path.join(distDir, cleanPath);

  // If path is a directory or does not exist, fall back to index.html (SPA client routing)
  if (!fs.existsSync(targetFile) || fs.statSync(targetFile).isDirectory()) {
    targetFile = path.join(distDir, 'index.html');
  }

  const ext = path.extname(targetFile).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  fs.readFile(targetFile, (err, content) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(`Internal Server Error: ${err.message}`);
      return;
    }
    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'no-cache',
    });
    res.end(content);
  });
});

server.listen(port, host, () => {
  console.log('\n  Páramo Urbano (v2.0.0 Core) — Frontend Server');
  console.log(`  ➜  Local:   http://localhost:${port}/`);
  console.log(`  ➜  Network: http://127.0.0.1:${port}/\n`);
});
