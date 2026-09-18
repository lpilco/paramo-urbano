"""Andean Outdoor Assistant domain service and knowledge base engine."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse

logger = logging.getLogger("AndeanAssistantService")


class AndeanAssistantService:
    """Intelligent assistant for Andean acclimatization, altitude preparation, and emergency escalation."""

    DEFAULT_WHATSAPP_PHONE: str = "593999999999"

    def __init__(self, knowledge_file_path: Optional[str] = None) -> None:
        """Initialize assistant service and load technical destination knowledge.

        Args:
            knowledge_file_path (Optional[str], optional): Path to destinos_andinos.json.
        """
        if knowledge_file_path:
            self._knowledge_path = knowledge_file_path
        else:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
            self._knowledge_path = os.path.join(root_dir, "data", "knowledge", "destinos_andinos.json")

        self._destinations: List[Dict[str, Any]] = self._load_knowledge()
        self._whatsapp_phone: str = os.getenv("WHATSAPP_SUPPORT_PHONE", self.DEFAULT_WHATSAPP_PHONE).lstrip("+")

    def _load_knowledge(self) -> List[Dict[str, Any]]:
        """Load and parse structured technical destination sheets from JSON file.

        Returns:
            List[Dict[str, Any]]: List of parsed destination dictionaries.
        """
        if not os.path.exists(self._knowledge_path):
            logger.warning(f"Knowledge base file not found at: {self._knowledge_path}")
            return []

        try:
            with open(self._knowledge_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} Andean destinations from knowledge base.")
                return data
        except Exception as err:
            logger.error(f"Failed to read Andean knowledge base: {err}")
            return []

    def get_destinations(self) -> List[Dict[str, Any]]:
        """Retrieve all structured Andean destination technical sheets.

        Returns:
            List[Dict[str, Any]]: Complete destination directory.
        """
        return list(self._destinations)

    def find_destination_by_name(self, query: str) -> Optional[Dict[str, Any]]:
        """Find a destination by exact or fuzzy keyword match.

        Args:
            query (str): Destination name or search keyword.

        Returns:
            Optional[Dict[str, Any]]: Destination technical sheet if found.
        """
        norm_query = query.lower().strip()
        for d in self._destinations:
            name = d.get("name", "").lower()
            dest_id = d.get("id", "").lower()
            if norm_query in name or norm_query in dest_id or any(part in norm_query for part in name.split()):
                return d
        return None

    def _detect_escalation_intent(self, text: str) -> Tuple[bool, str]:
        """Detect whether a query requires dynamic human or medical escalation to WhatsApp.

        Triggers:
            1. Guide hiring / contratación de guías ASEGUIM.
            2. Logistics / transporte 4x4 / arriendo de equipo.
            3. Severe Acute Mountain Sickness (MAM / AMS) symptoms.

        Args:
            text (str): Raw user message.

        Returns:
            Tuple[bool, str]: (should_escalate, reason)
        """
        lower = text.lower()

        # Severe Mountain Sickness (MAM) triggers (High Priority)
        mam_keywords = [
            "dolor de cabeza insoportable",
            "dolor de cabeza muy fuerte",
            "dolor de cabeza intenso",
            "vómito",
            "vomito",
            "vómitos",
            "vomitos",
            "náuseas intensas",
            "nauseas",
            "náusea",
            "no puedo respirar",
            "falta de aire en reposo",
            "tos con espuma",
            "mareo severo",
            "desorientado",
            "edema",
            "mal agudo de montaña",
            "mam severo",
        ]
        if any(kw in lower for kw in mam_keywords):
            return True, "EMERGENCIA_MEDICA_MAM"

        # Guide hiring triggers
        guide_keywords = [
            "guía",
            "guia",
            "contratar",
            "contratación",
            "aseguim",
            "servicio de guía",
            "guianza",
            "costo guía",
            "reserva de guía",
            "guía certificado",
        ]
        if any(kw in lower for kw in guide_keywords):
            return True, "CONTRATACION_GUIA"

        # Logistics & gear rental triggers
        logistics_keywords = [
            "logística",
            "logistica",
            "transporte",
            "alquiler de equipo",
            "alquilar botas",
            "alquilar crampones",
            "arriendo de equipo",
            "reserva refugio",
            "transporte 4x4",
            "traslado",
        ]
        if any(kw in lower for kw in logistics_keywords):
            return True, "LOGISTICA_AVANZADA"

        return False, "NONE"

    def generate_whatsapp_url(
        self,
        reason: str,
        user_message: str,
        destination_name: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a contextualized WhatsApp URL for seamless human operator handoff.

        Args:
            reason (str): Escalation reason ('EMERGENCIA_MEDICA_MAM', 'CONTRATACION_GUIA', 'LOGISTICA_AVANZADA').
            user_message (str): Original user query.
            destination_name (Optional[str], optional): Relevant mountain destination.
            user_profile (Optional[Dict[str, Any]], optional): User demographic context.

        Returns:
            str: Pre-formatted https://wa.me URL with URL-encoded text.
        """
        user_name = user_profile.get("full_name", "Atleta Páramo") if user_profile else "Atleta Páramo"
        user_level = user_profile.get("experience_level", "No especificado") if user_profile else "No especificado"

        dest_label = destination_name or "Destino Andino General"

        if reason == "EMERGENCIA_MEDICA_MAM":
            header = "🚨 *[ALERTA DE EMERGENCIA / SÍNTOMAS MAM - PÁRAMO URBANO]*"
            details = (
                f"{header}\n\n"
                f"👤 *Atleta:* {user_name} ({user_level})\n"
                f"⛰️ *Destino / Zona:* {dest_label}\n"
                f"⚠️ *Síntomas reportados:* {user_message}\n\n"
                f"Solicito asistencia de emergencia inmediata o protocolo de evacuación/oxigenoterapia."
            )
        elif reason == "CONTRATACION_GUIA":
            header = "🏔️ *[SOLICITUD DE GUÍA CERTIFICADO ASEGUIM - PÁRAMO URBANO]*"
            details = (
                f"{header}\n\n"
                f"👤 *Atleta:* {user_name} (Nivel: {user_level})\n"
                f"⛰️ *Destino de interés:* {dest_label}\n"
                f"📋 *Consulta:* {user_message}\n\n"
                f"Deseo coordinar disponibilidad, tarifas de cordada y fechas con un guía profesional acreditado."
            )
        else:
            header = "🎒 *[LOGÍSTICA Y EQUIPAMIENTO ANDINO - PÁRAMO URBANO]*"
            details = (
                f"{header}\n\n"
                f"👤 *Atleta:* {user_name} (Nivel: {user_level})\n"
                f"⛰️ *Destino:* {dest_label}\n"
                f"📋 *Requerimiento:* {user_message}\n\n"
                f"Solicito asesoría para reservas de refugio, transporte 4x4 o alquiler de equipo técnico homologado."
            )

        encoded_text = urllib.parse.quote(details)
        return f"https://wa.me/{self._whatsapp_phone}?text={encoded_text}"

    def process_chat(
        self,
        message: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process an incoming user message and formulate a scientific, grounded outdoor response.

        Args:
            message (str): Inbound athlete query.
            user_context (Optional[Dict[str, Any]], optional): Session or athlete profile context.

        Returns:
            Dict[str, Any]: Formatted response payload with escalation metadata.
        """
        clean_msg = message.strip()
        should_escalate, reason = self._detect_escalation_intent(clean_msg)

        # Detect destination in message or context
        matched_dest = None
        for d in self._destinations:
            name_parts = d["name"].lower().split()
            for part in name_parts:
                if len(part) > 4 and part in clean_msg.lower():
                    matched_dest = d
                    break
            if matched_dest:
                break

        dest_name = matched_dest.get("name") if matched_dest else None

        # Build response based on intent and content
        reply_paragraphs: List[str] = []

        if reason == "EMERGENCIA_MEDICA_MAM":
            reply_paragraphs.append(
                "🚨 **ALERTA CRÍTICA DE SALUD EN ALTITUD:** Los síntomas que describes "
                "(cefalea intensa, náuseas, vómitos o dificultad respiratoria) son signos evidentes de "
                "**Mal Agudo de Montaña (MAM)** con riesgo de progresión a Edema Pulmonar (HAPE) o Cerebral (HACE)."
            )
            reply_paragraphs.append(
                "**PROTOCOLO INMEDIATO:**\n"
                "1. **DETENER EL ASCENSO:** Nunca continúes ganando altura con síntomas.\n"
                "2. **DESCENSO:** El tratamiento definitivo y más eficaz es descender al menos 500 a 1.000 metros "
                "de inmediato.\n"
                "3. **HIDRATACIÓN Y ABRIGO:** Mantén calor corporal e ingiere líquidos calientes con electrolitos.\n"
                "4. **ASISTENCIA MÉDICA / RESCATE:** Hemos habilitado un enlace directo para contactar a los "
                "servicios de rescate y guías locales por WhatsApp."
            )
        elif matched_dest:
            reply_paragraphs.append(
                f"### Ficha Técnica: {matched_dest['name']} ({matched_dest['summit_elevation_m']} msnm)\n"
                f"* **Piso Altitudinal:** {matched_dest['altitudinal_floor']} "
                f"({matched_dest.get('altitudinal_range', '')})\n"
                f"* **Desnivel acumulado (+D):** +{matched_dest.get('elevation_gain_m', 0)} m\n"
                f"* **Ubicación:** {matched_dest.get('location_province', 'Ecuador')}"
            )

            # Check if query asks for gear
            if any(w in clean_msg.lower() for w in ("equipo", "material", "ropa", "botas", "crampon")):
                gear_list = "\n".join(f"- {g}" for g in matched_dest.get("mandatory_technical_gear", []))
                reply_paragraphs.append(f"**Equipamiento Técnico Obligatorio:**\n{gear_list}")

            # Check if query asks for acclimatization / hypoxia
            if any(w in clean_msg.lower() for w in ("aclimat", "oxigeno", "hipoxia", "altura", "prepar")):
                alerts = "\n".join(f"- {a}" for a in matched_dest.get("hypoxia_acclimatization_alerts", []))
                reply_paragraphs.append(f"**Pautas de Aclimatación e Hipoxia:**\n{alerts}")

            # Regulations & Guide
            guide_req = (
                "OBLIGATORIO (Guía ASEGUIM / UIAGM)" if matched_dest.get("aseguim_guide_mandatory") else "Recomendado"
            )
            reply_paragraphs.append(
                f"**Regulaciones MAATE y Guianza:**\n"
                f"- **Guía Profesional:** {guide_req}. {matched_dest.get('aseguim_notes', '')}\n"
                f"- **Requisitos Ambientales:** {', '.join(matched_dest.get('maate_requirements', []))}"
            )

            if should_escalate:
                reply_paragraphs.append(
                    f"Para coordinar guías certificados de la ASEGUIM o resolver traslados hacia el refugio de "
                    f"{matched_dest['name']}, presiona el botón inferior para conectarte vía WhatsApp con un "
                    f"operador oficial."
                )
        elif any(w in clean_msg.lower() for w in ("aclimat", "altura", "msnm", "hipoxia")):
            reply_paragraphs.append(
                "### Fisiología Andina: Principios Deterministas de Aclimatación\n"
                "Para entrenar y competir en la cordillera ecuatoriana con seguridad:\n\n"
                "1. **Regla 'Climb High, Sleep Low':** Realiza ascensiones progresivas de estímulo fisiológico "
                "durante el día, pero pernocta a menor altitud para favorecer la eritropoyesis sin fatiga hipóxica "
                "crónica.\n"
                "2. **Escalafón de Montañas en Ecuador:**\n"
                "   - *Fase 1 (Iniciación / 3.500-4.200 m):* Ilaló, Pasochoa o Cruz Loma.\n"
                "   - *Fase 2 (Media Montaña / 4.600-4.800 m):* Rucu Pichincha, Fuya Fuya o El Corazón.\n"
                "   - *Fase 3 (Transición / > 5.000 m):* Illiniza Norte o Guagua Pichincha.\n"
                "   - *Fase 4 (Alta Montaña Glaciar / > 5.800 m):* Cotopaxi, Cayambe o Chimborazo.\n"
                "3. **Hidratación:** En altitud, la ventilación acelerada deshidrata los alvéolos. Bebe entre "
                "3.5 y 4.5 L/día suplementados con sodio y magnesio."
            )
        elif any(w in clean_msg.lower() for w in ("desnivel", "+d", "fuerza", "vam", "pendiente")):
            reply_paragraphs.append(
                "### Preparación Física para Desnivel Positivo (+D)\n"
                "El desnivel en montaña demanda adaptaciones neuromusculares específicas:\n\n"
                "1. **Carga Excéntrica en Bajada:** El daño miofibrilar no ocurre en la subida, sino en los frenados "
                "excéntricos del descenso. En tu planificador, las sesiones de `STRENGTH` incluyen sentadillas "
                "búlgaras, desplantes y saltos pliométricos controlados.\n"
                "2. **Velocidad Ascensional Media (VAM):** Apunta a mantener una VAM sostenible de 400 a 600 m/h en "
                "pendientes del 15-25%, controlando que tu pulso se mantenga estrictamente en Zona 2 / Zona 3 "
                "aeróbica baja.\n"
                "3. **Uso Eficiente de Bastones:** Reduce el costo metabólico en las piernas hasta un 15-20% "
                "distribuyendo el impulso hacia el dorsal ancho y la cintura escapular."
            )
        else:
            reply_paragraphs.append(
                "¡Hola! Soy tu **Asistente Outdoor Andino** de Páramo Urbano. Estoy especializado en la geografía "
                "de montaña de Ecuador y en la fisiología de altitud.\n\n"
                "Puedo orientarte con precisión sobre:\n"
                "- **Fichas Técnicas de Destinos:** Rucu Pichincha, Corazón, Illiniza Norte, Cotopaxi, Chimborazo y "
                "Cayambe.\n"
                "- **Equipamiento Obligatorio:** Requisitos técnicos de glaciar y media montaña.\n"
                "- **Aclimatación y Prevención:** Estrategias escalonadas contra el Mal Agudo de Montaña (MAM).\n"
                "- **Regulaciones MAATE y Guías ASEGUIM:** Normativa legal para ingreso a parques nacionales.\n\n"
                "*¿Qué cumbre o travesía andina deseas preparar hoy?*"
            )

        reply_text = "\n\n".join(reply_paragraphs)
        whatsapp_url = None
        if should_escalate:
            whatsapp_url = self.generate_whatsapp_url(
                reason=reason,
                user_message=clean_msg,
                destination_name=dest_name,
                user_profile=user_context,
            )

        return {
            "reply": reply_text,
            "escalate_to_whatsapp": should_escalate,
            "escalation_reason": reason,
            "whatsapp_url": whatsapp_url,
            "destination": matched_dest,
        }
