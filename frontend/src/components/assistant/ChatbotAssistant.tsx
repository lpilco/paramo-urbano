/**
 * @fileoverview Andean Outdoor Assistant floating widget and chat interface.
 * Provides high-altitude intelligence, technical peak sheets, and dynamic WhatsApp escalation.
 * @module components/assistant/ChatbotAssistant
 */

import React, { useState, useRef, useEffect } from 'react';
import { sendAssistantMessage } from '../../api/assistantApi';
import type { ChatResponse, DestinationSheet } from '../../types';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  escalateToWhatsapp?: boolean;
  escalationReason?: string | null;
  whatsappUrl?: string | null;
  destination?: DestinationSheet | null;
}

const QUICK_PROMPTS = [
  'Equipamiento para Cotopaxi',
  'Aclimatación Rucu Pichincha',
  'Síntomas de Mal de Altura (MAM)',
  'Contratar Guía ASEGUIM',
  'Desnivel positivo y fuerza excéntrica',
];

/**
 * Parses markdown-like text (bold, bullet points, headers) safely into React elements.
 *
 * @param {string} text - Raw markdown text
 * @returns {React.ReactNode}
 */
function renderFormattedMessage(text: string): React.ReactNode {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = () => {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-1 pl-4 list-disc">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const formatInline = (str: string): React.ReactNode[] => {
    // Matches **bold**
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={idx}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }

    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${idx}`} className="font-bold text-sm text-sky-400 mt-2 mb-1">
          {formatInline(trimmed.replace('### ', ''))}
        </h3>
      );
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true;
      listItems.push(
        <li key={`li-${idx}`} className="text-xs text-slate-200">
          {formatInline(trimmed.slice(2))}
        </li>
      );
    } else {
      flushList();
      elements.push(
        <p key={`p-${idx}`} className="text-xs text-slate-200 my-1">
          {formatInline(trimmed)}
        </p>
      );
    }
  });

  flushList();
  return elements;
}

/**
 * Andean Outdoor Assistant floating interactive chatbot component.
 *
 * @returns {JSX.Element}
 */
export const ChatbotAssistant: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: '¡Hola! Soy tu **Asistente Outdoor Andino** de Páramo Urbano.\n\nPuedo orientarte sobre:\n- **Fichas Técnicas de Cumbres:** Cotopaxi, Chimborazo, Cayambe, Rucu Pichincha, etc.\n- **Equipamiento Técnico Obligatorio** y pautas de altitud.\n- **Prevención de Mal Agudo de Montaña (MAM).**\n- **Contratación directa de guías certificados ASEGUIM.**\n\n¿En qué cumbre o entrenamiento te puedo ayudar hoy?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response: ChatResponse = await sendAssistantMessage(query);

      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        escalateToWhatsapp: response.escalate_to_whatsapp,
        escalationReason: response.escalation_reason,
        whatsappUrl: response.whatsapp_url,
        destination: response.destination,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch {
      const errorMessage: Message = {
        id: `bot-err-${Date.now()}`,
        sender: 'assistant',
        text: 'Lo siento, ocurrió un error de comunicación con el servicio de montaña. Por favor verifica tu conexión o intenta nuevamente.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        type="button"
        className="assistant-fab"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Cerrar Asistente Andino' : 'Abrir Asistente Andino'}
        title="Asistente Outdoor Andino"
      >
        <span className="assistant-fab-icon" aria-hidden="true">
          🏔️
        </span>
        <span>{isOpen ? 'Cerrar' : 'Asistente Andino'}</span>
      </button>

      {/* Expandable Chat Window */}
      {isOpen && (
        <section
          className="assistant-chat-window"
          role="dialog"
          aria-labelledby="assistant-title"
          aria-modal="false"
        >
          {/* Header */}
          <header className="assistant-chat-header">
            <div>
              <div className="assistant-header-title" id="assistant-title">
                <span aria-hidden="true">⛰️</span>
                <span>Asistente Outdoor Andino</span>
              </div>
              <div className="assistant-header-subtitle">
                Geografía ecuatoriana & fisiología de altitud
              </div>
            </div>
            <button
              type="button"
              className="assistant-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Cerrar ventana de asistente"
            >
              ✕
            </button>
          </header>

          {/* Messages Body */}
          <div className="assistant-messages-body">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`assistant-msg-row ${msg.sender}`}
              >
                <div
                  className={`assistant-avatar ${msg.sender === 'user' ? 'user' : 'bot'}`}
                  aria-hidden="true"
                >
                  {msg.sender === 'user' ? 'Tú' : 'PU'}
                </div>
                <div className="assistant-bubble">
                  {renderFormattedMessage(msg.text)}

                  {/* Destination Mini-Badge */}
                  {msg.destination && (
                    <div className="mt-2 pt-2 border-t border-slate-700 text-xs text-slate-300">
                      <div>
                        📍 <strong>{msg.destination.name}</strong> ({msg.destination.summit_elevation_m} msnm)
                      </div>
                      <div className="text-slate-400 text-[11px] mt-0.5">
                        {msg.destination.location_province} • Piso: {msg.destination.altitudinal_floor}
                      </div>
                    </div>
                  )}

                  {/* WhatsApp Escalation Card */}
                  {msg.escalateToWhatsapp && msg.whatsappUrl && (
                    <div
                      className={`assistant-escalation-card ${
                        msg.escalationReason === 'EMERGENCIA_MEDICA_MAM' ? 'emergency' : ''
                      }`}
                    >
                      <div className="assistant-escalation-text">
                        {msg.escalationReason === 'EMERGENCIA_MEDICA_MAM'
                          ? '⚠️ Protocolo de Emergencia en Altura activo'
                          : '🏔️ Coordinación directa con guías autorizados ASEGUIM'}
                      </div>
                      <a
                        href={msg.whatsappUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="assistant-whatsapp-btn"
                      >
                        <span aria-hidden="true">💬</span>
                        <span>Contactar por WhatsApp</span>
                      </a>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="assistant-msg-row assistant">
                <div className="assistant-avatar bot" aria-hidden="true">
                  PU
                </div>
                <div className="assistant-bubble text-slate-400 italic text-xs">
                  Analizando cartografía y fisiología andina...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts Bar */}
          <div className="assistant-quick-container" aria-label="Preguntas rápidas">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="assistant-quick-chip"
                onClick={() => handleSendMessage(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <footer className="assistant-input-area">
            <input
              type="text"
              className="assistant-input-field"
              placeholder="Consulta sobre cumbres, equipo, hipoxia..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              aria-label="Escribe tu mensaje para el asistente andino"
            />
            <button
              type="button"
              className="assistant-send-btn"
              onClick={() => handleSendMessage()}
              disabled={loading || !inputMessage.trim()}
              aria-label="Enviar mensaje"
            >
              ➤
            </button>
          </footer>
        </section>
      )}
    </>
  );
};
