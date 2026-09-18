/**
 * @fileoverview Unit tests for ChatbotAssistant component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatbotAssistant } from '../src/components/assistant/ChatbotAssistant';
import * as assistantApi from '../src/api/assistantApi';

vi.mock('../src/api/assistantApi');

describe('ChatbotAssistant Component (P1 Andean Intelligence)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders floating action button in closed state', () => {
    render(<ChatbotAssistant />);

    const fab = screen.getByRole('button', { name: /Abrir Asistente Andino/i });
    expect(fab).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('opens and closes chat dialog when FAB is clicked', () => {
    render(<ChatbotAssistant />);

    const fab = screen.getByRole('button', { name: /Abrir Asistente Andino/i });
    fireEvent.click(fab);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getAllByText(/Asistente Outdoor Andino/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/¡Hola! Soy tu/i)).toBeInTheDocument();

    const closeBtn = screen.getByRole('button', { name: /Cerrar ventana de asistente/i });
    fireEvent.click(closeBtn);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('sends user message and renders assistant reply with destination card', async () => {
    vi.mocked(assistantApi.sendAssistantMessage).mockResolvedValueOnce({
      reply: 'Ficha Técnica: Rucu Pichincha a 4696 msnm',
      escalate_to_whatsapp: false,
      destination: {
        id: 'rucu_pichincha',
        name: 'Rucu Pichincha',
        altitudinal_floor: 'PÁRAMO_ANDINO',
        altitudinal_range: '3.800 - 4.696 msnm',
        summit_elevation_m: 4696,
        elevation_gain_m: 750,
        location_province: 'Pichincha',
        approach_refuges: [],
        mandatory_technical_gear: ['Casco'],
        hypoxia_acclimatization_alerts: [],
        maate_requirements: [],
        aseguim_guide_mandatory: false,
        aseguim_notes: 'Recomendado',
        recommended_season: 'Junio a Septiembre',
      },
    });

    render(<ChatbotAssistant />);
    fireEvent.click(screen.getByRole('button', { name: /Abrir Asistente Andino/i }));

    const input = screen.getByPlaceholderText(/Consulta sobre cumbres/i);
    fireEvent.change(input, { target: { value: '¿Qué altura tiene Rucu Pichincha?' } });

    const sendBtn = screen.getByRole('button', { name: /Enviar mensaje/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/Ficha Técnica: Rucu Pichincha a 4696 msnm/i)).toBeInTheDocument();
      expect(screen.getAllByText(/4696 msnm/i)[0]).toBeInTheDocument();
    });
  });

  it('renders WhatsApp escalation CTA when severe MAM symptoms or guide hiring is detected', async () => {
    vi.mocked(assistantApi.sendAssistantMessage).mockResolvedValueOnce({
      reply: 'ALERTA CRÍTICA DE SALUD EN ALTITUD: Síntomas de MAM detectados.',
      escalate_to_whatsapp: true,
      escalation_reason: 'EMERGENCIA_MEDICA_MAM',
      whatsapp_url: 'https://wa.me/593999999999?text=Emergencia',
    });

    render(<ChatbotAssistant />);
    fireEvent.click(screen.getByRole('button', { name: /Abrir Asistente Andino/i }));

    const promptChip = screen.getByText('Síntomas de Mal de Altura (MAM)');
    fireEvent.click(promptChip);

    await waitFor(() => {
      expect(screen.getByText(/ALERTA CRÍTICA DE SALUD EN ALTITUD/i)).toBeInTheDocument();
      const whatsappLink = screen.getByRole('link', { name: /Contactar por WhatsApp/i });
      expect(whatsappLink).toHaveAttribute('href', 'https://wa.me/593999999999?text=Emergencia');
      expect(whatsappLink).toHaveAttribute('target', '_blank');
    });
  });
});
