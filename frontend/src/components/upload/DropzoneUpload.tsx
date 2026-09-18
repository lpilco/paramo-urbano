/**
 * @fileoverview DropzoneUpload component with in-memory Web Crypto SHA-256 calculation and async polling.
 * @module components/upload/DropzoneUpload
 */

import React, { useState, useRef, useCallback } from 'react';
import { uploadActivityFile, getJobStatus } from '../../api/activitiesApi';
import { ApiError } from '../../api/apiClient';
import type { UploadActivityResponse } from '../../types';

export interface DropzoneUploadProps {
  onUploadSuccess?: (result: UploadActivityResponse) => void;
  onUploadError?: (error: string) => void;
}

export interface FileProcessingState {
  file: File;
  sha256: string;
  progress: number;
  status: 'hashing' | 'uploading' | 'queued' | 'processed' | 'error';
  jobId?: string;
  errorMessage?: string;
}

/**
 * Computes SHA-256 hash in memory using native browser Web Crypto API.
 * @async
 * @param {File} file
 * @returns {Promise<string>} Hexadecimal SHA-256 string
 */
export async function computeFileSha256(file: File): Promise<string> {
  let buffer: ArrayBuffer;
  if (typeof file.arrayBuffer === 'function') {
    buffer = await file.arrayBuffer();
  } else {
    buffer = await new Promise<ArrayBuffer>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as ArrayBuffer);
      reader.onerror = () => reject(new Error('Failed to read file as ArrayBuffer'));
      reader.readAsArrayBuffer(file);
    });
  }
  const digestBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(digestBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

export const DropzoneUpload: React.FC<DropzoneUploadProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [activeItems, setActiveItems] = useState<FileProcessingState[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(
    async (file: File) => {
      // 1. Validation of size (25 MB max)
      const MAX_BYTES = 25 * 1024 * 1024;
      if (file.size > MAX_BYTES) {
        const err = `El archivo "${file.name}" supera el límite máximo de 25 MB.`;
        onUploadError?.(err);
        return;
      }

      // Initial state
      const item: FileProcessingState = {
        file,
        sha256: 'Calculando...',
        progress: 10,
        status: 'hashing',
      };
      setActiveItems((prev) => [item, ...prev]);

      try {
        // 2. Compute SHA-256 in memory
        const sha256 = await computeFileSha256(file);
        setActiveItems((prev) =>
          prev.map((i) =>
            i.file === file ? { ...i, sha256, progress: 40, status: 'uploading' } : i
          )
        );

        // 3. Send multipart upload to backend (HTTP 202)
        const response = await uploadActivityFile(file);

        setActiveItems((prev) =>
          prev.map((i) =>
            i.file === file
              ? {
                  ...i,
                  jobId: response.job_id,
                  progress: 80,
                  status: 'queued',
                }
              : i
          )
        );

        // 4. Reactive polling of job status from worker
        const pollJobStatus = () => {
          const maxAttempts = 40; // 40 * 750ms = 30s max
          let attempts = 0;

          const interval = setInterval(async () => {
            attempts += 1;
            try {
              const statusData = await getJobStatus(response.job_id);
              const progressPct = Math.max(50, Math.min(100, statusData.progress_percent || 60));

              if (statusData.status === 'COMPLETED') {
                clearInterval(interval);
                setActiveItems((prev) =>
                  prev.map((i) =>
                    i.file === file
                      ? {
                          ...i,
                          progress: 100,
                          status: 'processed',
                        }
                      : i
                  )
                );
                onUploadSuccess?.(response);
              } else if (statusData.status === 'FAILED') {
                clearInterval(interval);
                const errMsg = statusData.error_message || 'El procesamiento del archivo falló.';
                setActiveItems((prev) =>
                  prev.map((i) =>
                    i.file === file
                      ? {
                          ...i,
                          progress: 100,
                          status: 'error',
                          errorMessage: errMsg,
                        }
                      : i
                  )
                );
                onUploadError?.(errMsg);
              } else {
                setActiveItems((prev) =>
                  prev.map((i) =>
                    i.file === file
                      ? {
                          ...i,
                          progress: progressPct,
                          status: statusData.status === 'PROCESSING' ? 'uploading' : 'queued',
                        }
                      : i
                  )
                );
              }
            } catch {
              // Network retry or job still initializing
            }

            if (attempts >= maxAttempts) {
              clearInterval(interval);
              setActiveItems((prev) =>
                prev.map((i) =>
                  i.file === file
                    ? {
                        ...i,
                        progress: 100,
                        status: 'processed',
                      }
                    : i
                )
              );
              onUploadSuccess?.(response);
            }
          }, 750);
        };

        pollJobStatus();
      } catch (err: unknown) {
        let msg = 'Error inesperado al subir archivo.';
        if (err instanceof ApiError) {
          if (err.status === 409) {
            msg = `Archivo duplicado: "${file.name}" ya fue procesado con anterioridad.`;
          } else if (err.status === 422) {
            msg = `Archivo corrupto o formato no válido: ${err.detail}`;
          } else {
            msg = err.detail || err.message;
          }
        } else if (err instanceof Error) {
          msg = err.message;
        }

        setActiveItems((prev) =>
          prev.map((i) =>
            i.file === file
              ? {
                  ...i,
                  progress: 100,
                  status: 'error',
                  errorMessage: msg,
                }
              : i
          )
        );
        onUploadError?.(msg);
      }
    },
    [onUploadSuccess, onUploadError]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    files.forEach((f) => processFile(f));
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      files.forEach((f) => processFile(f));
    }
  };

  return (
    <section className="dropzone-section" aria-labelledby="dropzone-heading">
      <h3 id="dropzone-heading" className="visually-hidden" style={{ display: 'none' }}>
        Contenedor de Ingesta Asíncrona de Telemetría
      </h3>

      <div
        className={`dropzone-box ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Zona de arrastre para archivos de telemetría .FIT, .GPX o .CSV"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            fileInputRef.current?.click();
          }
        }}
        style={{
          border: `2px dashed ${isDragging ? 'var(--accent-summit)' : 'var(--border-strong)'}`,
          background: isDragging ? 'rgba(255, 107, 53, 0.08)' : 'var(--bg-input)',
          borderRadius: 'var(--radius-md)',
          padding: '2.5rem 1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all var(--transition-fast)',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".fit,.gpx,.csv,.json"
          multiple
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          id="telemetry-file-input"
        />

        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }} aria-hidden="true">
          🏔️
        </div>
        <h4 style={{ fontSize: '1.1rem', marginBottom: '0.35rem' }}>
          Arrastra aquí tus archivos de entrenamiento
        </h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Soporta formatos binarios <strong>.FIT</strong> (Garmin/Polar/Suunto), <strong>.GPX</strong>, <strong>.CSV</strong> y <strong>.JSON</strong>
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
          Límite de hasta 25 MB por archivo • Cálculo criptográfico SHA-256 en memoria
        </p>

        <button
          type="button"
          className="btn btn-secondary"
          style={{ marginTop: '1rem', pointerEvents: 'none' }}
          tabIndex={-1}
        >
          Explorar archivos locales
        </button>
      </div>

      {/* Reactive File Progress List */}
      {activeItems.length > 0 && (
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {activeItems.map((item, index) => (
            <article
              key={`${item.file.name}-${index}`}
              className="card"
              style={{ padding: '0.85rem 1.25rem' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                    {item.file.name}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.7rem',
                      color: 'var(--text-muted)',
                      letterSpacing: '0.02em',
                    }}
                  >
                    SHA-256: {item.sha256}
                  </span>
                </div>

                <div>
                  {item.status === 'hashing' && (
                    <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-glacier)' }}>
                      Criptografía...
                    </span>
                  )}
                  {item.status === 'uploading' && (
                    <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)' }}>
                      Subiendo...
                    </span>
                  )}
                  {item.status === 'queued' && (
                    <span className="badge badge-sweet-spot">
                      En Cola (HTTP 202)
                    </span>
                  )}
                  {item.status === 'processed' && (
                    <span className="badge badge-sweet-spot">
                      ✓ Procesado
                    </span>
                  )}
                  {item.status === 'error' && (
                    <span className="badge badge-danger">
                      ✕ Falló
                    </span>
                  )}
                </div>
              </div>

              {/* Progress bar */}
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  background: 'var(--border-subtle)',
                  borderRadius: 'var(--radius-pill)',
                  marginTop: '0.75rem',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${item.progress}%`,
                    height: '100%',
                    background:
                      item.status === 'error'
                        ? 'var(--acwr-danger)'
                        : 'linear-gradient(90deg, var(--accent-summit), var(--accent-glacier))',
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>

              {item.errorMessage && (
                <p style={{ fontSize: '0.75rem', color: 'var(--acwr-danger)', marginTop: '0.4rem' }}>
                  {item.errorMessage}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
