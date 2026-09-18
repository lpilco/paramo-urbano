---
name: frontend-standards
description: >-
  Estándares y directrices para desarrollo frontend moderno (HTML5 & JavaScript ESM): HTML semántico estricto (cero divitis), accesibilidad universal (WCAG 2.1 AA), arquitectura modular sin framework o vanilla, separación de responsabilidades, tipado y documentación con JSDoc exhaustivo.
---

# Guía de Estilo y Estándares para Desarrollo Frontend (HTML5 & JavaScript)

> **Rol del Agente / Desarrollador:** Ingeniero de Software Frontend Senior especializado en estándares web modernos. Cada fragmento de código HTML y JavaScript debe cumplir estrictamente con los estándares W3C/WHATWG, accesibilidad (WCAG 2.1 AA), modularidad ECMAScript (ESM), clean code y documentación exhaustiva mediante JSDoc.

---

## 1. Regla Mandatoria: HTML Semántico Estricto y Accesibilidad Universal (A11y / W3C)

* **Cero "Divitis" o "Spanitis":** Queda prohibido el uso indiscriminado de `<div>` y `<span>` para elementos que poseen un equivalente semántico nativo.
* **Jerarquía de Landmarks Obligatoria:** Todo documento o vista principal debe delimitar sus regiones mediante etiquetas semánticas:
  * `<header>`: Encabezado contextual o global.
  * `<nav>`: Bloque de enlaces de navegación primaria o paginación (debe incluir `aria-label` si coexisten varios `<nav>`).
  * `<main>`: Contenedor único del contenido central y exclusivo del documento (solo uno visible por vista).
  * `<section>`: Agrupación temática de contenido, idealmente con su propio encabezado (`<h2>`-`<h6>`).
  * `<article>`: Unidad de contenido autónoma y reutilizable (ej. tarjetas de métricas, posts, comentarios).
  * `<aside>`: Contenido secundario, barras laterales o relaciones tangenciales.
  * `<footer>`: Pie de página contextual o global.
* **Formularios Accesibles:**
  * Todo `<input>`, `<textarea>` y `<select>` debe tener un `<label>` asociado explícitamente mediante `for="input-id"` o contención directa.
  * Los mensajes de error o descripciones complementarias deben vincularse con `aria-describedby="error-id"`.
* **Imágenes y Multimedia:** Toda etiqueta `<img>` debe contar con un atributo `alt` descriptivo. Si la imagen es puramente decorativa, declarar explícitamente `alt=""` y `aria-hidden="true"`.
* **Botones vs Enlaces:**
  * Usa `<a>` exclusivamente para navegación y cambio de URL.
  * Usa `<button type="button|submit|reset">` para acciones que desencadenan eventos o manipulación del DOM.

---

## 2. Regla Mandatoria: Principio DRY y Arquitectura Basada en Módulos (ESM)

* **Uso Exclusivo de Módulos ES6 (`import` / `export`):**
  * Prohibida la contaminación del scope global (`window.*`).
  * Las etiquetas `<script>` en HTML deben incluir siempre el atributo `type="module"` o ser cargadas de forma diferida (`defer`).
* **Cero Duplicación de Lógica en el DOM:**
  * Centraliza selectores recurrentes del DOM, configuraciones y llamadas de red.
  * Si un cálculo, formateo (monedas, fechas, distancias) o sanitización de datos se repite, debe encapsularse en un módulo de utilidades (`/utils/`).
* **Separación Estricta de Responsabilidades:**
  * **HTML:** Estructura y semántica. Quedan prohibidos los estilos en línea (`style="..."`) y eventos embebidos (`onclick="..."`).
  * **CSS:** Presentación y diseño visual.
  * **JS:** Comportamiento, reactividad e integración con APIs.

---

## 3. Regla Mandatoria: Principio *Do One Thing* y Gestión de Estado

* **Una Sola Tarea por Función:**
  * Separa estrictamente la **adquisición de datos** (`fetch`, API calls), de la **transformación de datos**, de la **mutación/renderizado en el DOM**.
  * ❌ *Antipatrón:* Una función `cargarYRenderizarUsuarios()` que hace el fetch, filtra un array y añade elementos con `innerHTML`.
  * ✔️ *Patrón Correcto:* `obtenerUsuarios()`, `filtrarUsuariosActivos()` y `renderizarListaUsuarios()`.
* **Inmutabilidad de Datos:** Evita mutar parámetros o estructuras de datos recibidas; favorece métodos declarativos e inmutables como `.map()`, `.filter()`, `.reduce()` o el operador spread (`...`).
* **Gestión Segura del DOM:**
  * Prohibido el uso inseguro de `element.innerHTML` con datos no sanitizados provenientes del usuario o de APIs de terceros (prevención de vulnerabilidades XSS).
  * Prefiere `element.textContent`, `document.createElement()`, `<template>` o librerías de sanitización dedicadas si se requiere inyectar HTML.

---

## 4. Regla Mandatoria: Documentación Estándar JSDoc

Toda función pública, método de clase o constante exportada debe documentarse mediante un bloque JSDoc (`/** ... */`) inmediatamente antes de su declaración:

### Estructura Requerida:

1. **Descripción concisa (Modo Imperativo):** Inicia con un verbo en imperativo describiendo la acción exacta (ej. *"Fetch user profile details from API..."*).
2. **@async (si aplica):** Obligatorio para funciones asíncronas o que retornan promesas.
3. **@param {Tipo} nombre - Descripción:** Lista cada parámetro, su tipo de dato (incluyendo tipos compuestos como `Object`, `Array<string>`, o `HTMLElement`), y su propósito.
   * Si es opcional, indicar entre corchetes con valor por defecto: `[param=defaultValue]`.
4. **@returns {Tipo} Descripción:** Tipo de dato retornado y qué representa. Omitir solo si la función retorna `void`.
5. **@throws {TipoDeError} Condición:** Excepciones que la función lanza deliberadamente o errores de red no manejados.
6. **@example (Opcional):** Ejemplo breve de invocación en casos de lógica compleja.

---

## 5. Plantillas Canónicas de Referencia

### 5.1 Estructura HTML5 Semántica (`index.html`)

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Dashboard de gestión y métricas de proyectos.">
  <title>Métricas de Proyectos | Enterprise Portal</title>
  <link rel="stylesheet" href="./styles/main.css">
  <script type="module" src="./src/main.js"></script>
</head>
<body>

  <!-- ==========================================
       HEADER / NAVEGACIÓN PRINCIPAL
       ========================================== -->
  <header role="banner" class="site-header">
    <nav class="nav-container" aria-label="Navegación principal">
      <a href="/" class="brand-link" aria-label="Ir a página de inicio">
        <img src="./assets/logo.svg" alt="Logotipo de la plataforma" width="140" height="36">
      </a>
      <ul class="nav-menu" role="list">
        <li><a href="#metricas" class="nav-link">Métricas</a></li>
        <li><a href="#proyectos" class="nav-link">Proyectos</a></li>
      </ul>
    </nav>
  </header>

  <!-- ==========================================
       CONTENIDO PRINCIPAL
       ========================================== -->
  <main id="main-content" class="content-container">

    <section id="metricas" class="section-block" aria-labelledby="heading-metricas">
      <h1 id="heading-metricas" class="section-title">Resumen de Rendimiento</h1>

      <!-- Componente Card de Métricas -->
      <article class="metric-card" data-metric-type="throughput">
        <header class="metric-card-header">
          <h2 class="metric-title">Tasa de Procesamiento</h2>
        </header>
        <div class="metric-body">
          <p class="metric-value" id="throughput-value" aria-live="polite">Cargando...</p>
        </div>
      </article>
    </section>

    <!-- Formulario con accesibilidad declarativa -->
    <section id="filtro-proyectos" class="section-block" aria-labelledby="heading-filtro">
      <h2 id="heading-filtro" class="section-title">Buscar Proyectos</h2>

      <form id="search-form" class="form-group" novalidate>
        <label for="project-search-input" class="form-label">Término de búsqueda</label>
        <input 
          type="search" 
          id="project-search-input" 
          name="query" 
          class="form-input" 
          placeholder="Ej. Transcodificador" 
          aria-describedby="search-hint"
          required
        >
        <span id="search-hint" class="input-hint">Presione Enter para ejecutar la búsqueda.</span>
        <button type="submit" class="btn btn-primary">Buscar</button>
      </form>
    </section>

  </main>

  <!-- ==========================================
       PIE DE PÁGINA
       ========================================== -->
  <footer role="contentinfo" class="site-footer">
    <p class="copyright">© 2026 Enterprise Inc. Todos los derechos reservados.</p>
  </footer>

</body>
</html>
```

### 5.2 Estándar JavaScript Modular con JSDoc (`src/services/metrics.service.js`)

```javascript
/**
 * @fileoverview Servicio para obtención y cálculo de métricas de rendimiento.
 * @module services/metrics
 */

/**
 * Representa la respuesta de métricas procesadas.
 * @typedef {Object} MetricPayload
 * @property {string} id - Identificador único de la métrica.
 * @property {number} value - Valor numérico calculado.
 * @property {string} unit - Unidad de medida (ej. "req/s", "ms").
 */

/**
 * Retrieve performance metrics from the internal API.
 *
 * Performs a network request with an automatic abort signal if
 * the configured timeout expires.
 *
 * @async
 * @param {string} endpoint - The target API URL or path.
 * @param {number} [timeoutMs=5000] - Request timeout window in milliseconds. Defaults to 5000.
 * @returns {Promise<MetricPayload>} The parsed metric payload.
 * @throws {TypeError} If the endpoint parameter is not a non-empty string.
 * @throws {Error} If the server returns an HTTP status outside the 200-299 range or times out.
 * 
 * @example
 * const metric = await fetchSystemMetric('/api/v1/health/throughput');
 * console.log(`Throughput: ${metric.value} ${metric.unit}`);
 */
export async function fetchSystemMetric(endpoint, timeoutMs = 5000) {
  if (!endpoint || typeof endpoint !== 'string' || endpoint.trim() === '') {
    throw new TypeError('Parameter "endpoint" must be a non-empty string.');
  }

  const controller = new AbortController();
  const timeoutTimer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: Failed to fetch "${endpoint}"`);
    }

    /** @type {MetricPayload} */
    const data = await response.json();
    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request to "${endpoint}" timed out after ${timeoutMs}ms.`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutTimer);
  }
}

/**
 * Format raw throughput metrics into localized, readable text.
 *
 * @param {number} value - The numerical throughput rate.
 * @param {string} [locale='es-ES'] - BCP 47 language tag for internationalization. Defaults to 'es-ES'.
 * @returns {string} Formatted number with localized decimal and grouping separators.
 * @throws {TypeError} If value is not a finite number.
 */
export function formatThroughputRate(value, locale = 'es-ES') {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError('Parameter "value" must be a finite number.');
  }

  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  }).format(value);
}
```

### 5.3 Controlador de Vista y Manejo de Eventos (`src/main.js`)

```javascript
/**
 * @fileoverview Punto de entrada de la aplicación.
 * Orquesta la inicialización del DOM y el enlace de eventos.
 * @module main
 */

import { fetchSystemMetric, formatThroughputRate } from './services/metrics.service.js';

/**
 * Update the throughput card UI with real-time data.
 *
 * @async
 * @param {HTMLElement} targetElement - DOM element where the result will be printed.
 * @returns {Promise<void>}
 */
async function updateThroughputDisplay(targetElement) {
  if (!(targetElement instanceof HTMLElement)) {
    throw new TypeError('Target element must be a valid HTMLElement instance.');
  }

  try {
    const metric = await fetchSystemMetric('/api/v1/health/throughput');
    const formattedValue = formatThroughputRate(metric.value);

    // Asignación segura de texto evitando vulnerabilidades XSS
    targetElement.textContent = `${formattedValue} ${metric.unit}`;
  } catch (error) {
    console.error('[Dashboard Error]:', error.message);
    targetElement.textContent = 'Error al cargar métricas';
    targetElement.classList.add('text-danger');
  }
}

/**
 * Initialize application listeners and kickstart view rendering.
 *
 * @returns {void}
 */
function initializeApp() {
  const throughputEl = document.getElementById('throughput-value');
  const searchFormEl = document.getElementById('search-form');

  if (throughputEl) {
    updateThroughputDisplay(throughputEl);
  }

  if (searchFormEl) {
    searchFormEl.addEventListener('submit', (event) => {
      event.preventDefault();
      const formData = new FormData(searchFormEl);
      const query = String(formData.get('query') || '').trim();

      if (query) {
        console.info(`Ejecutando búsqueda para: "${query}"`);
      }
    });
  }
}

// Asegurar ejecución solo tras la carga completa del DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
```

---

## 6. Prácticas Complementarias de Código Limpio

### Prevención de Fugas de Memoria (*Memory Leaks*)
Todo *event listener* asignado a elementos dinámicos que se destruyen con frecuencia debe ser removido explícitamente (`removeEventListener`) o manejado con controladores abortables (`{ signal: abortController.signal }`).

### Cero Dependencias Innecesarias
Aprovecha las APIs modernas nativas de los navegadores (`fetch`, `Intl`, `FormData`, `AbortController`, `structuredClone`) antes de importar librerías pesadas externas.

### Gestión de Variables de Entorno en Frontend
* Nunca almacenes secretos reales (claves privadas de base de datos, tokens de administración) en el cliente.
* Las variables públicas de configuración de frontend deben inyectarse mediante herramientas de compilación modernas (`import.meta.env.VITE_*` en Vite o `process.env.NEXT_PUBLIC_*` en Next.js) y documentarse en un archivo `.env.example`.
