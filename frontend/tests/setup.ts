import '@testing-library/jest-dom';
import { webcrypto } from 'node:crypto';

// Polyfill Web Crypto API for jsdom if needed
try {
  if (!globalThis.crypto || !globalThis.crypto.subtle) {
    Object.defineProperty(globalThis, 'crypto', {
      value: webcrypto,
      writable: true,
      configurable: true,
    });
  }
} catch {
  // Native webcrypto already active in modern Node.js
}

// Polyfill Blob/File arrayBuffer if missing in jsdom
if (typeof Blob !== 'undefined' && !Blob.prototype.arrayBuffer) {
  Blob.prototype.arrayBuffer = function () {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(this);
    });
  };
}

if (typeof File !== 'undefined' && !File.prototype.arrayBuffer) {
  File.prototype.arrayBuffer = function () {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(this);
    });
  };
}

// Polyfill scrollTo
window.scrollTo = () => {};
