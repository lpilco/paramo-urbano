/**
 * @fileoverview Andean Outdoor Assistant API client.
 * @module api/assistantApi
 */

import { apiFetch } from './apiClient';
import type { ChatRequest, ChatResponse, DestinationSheet } from '../types';

/**
 * Send query to Andean Outdoor Assistant for destination intel, acclimatization and escalation.
 *
 * @async
 * @param {string} message - User query or question
 * @param {Record<string, unknown>} [context] - Optional user context
 * @returns {Promise<ChatResponse>} Formatted response with escalation metadata
 */
export async function sendAssistantMessage(
  message: string,
  context?: Record<string, unknown>
): Promise<ChatResponse> {
  const payload: ChatRequest = { message, context };
  return apiFetch<ChatResponse>('/assistant/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Fetch complete catalog of Andean mountain destination sheets.
 *
 * @async
 * @returns {Promise<{ destinations: DestinationSheet[] }>} Catalog of mountains
 */
export async function getDestinationsCatalog(): Promise<{ destinations: DestinationSheet[] }> {
  return apiFetch<{ destinations: DestinationSheet[] }>('/assistant/destinations', {
    method: 'GET',
  });
}
