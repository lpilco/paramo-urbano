---
name: python-coding-standards
description: >-
  Estándares de estilo y desarrollo para Python en el proyecto: cero hardcoding, gestión segura de secretos (.env), principio DRY, principio de responsabilidad única (Do One Thing), Google-style docstrings y aislamiento de ejecución.
---

# Guía de Estilo y Estándares de Codificación en Python

> **Rol del Agente / Desarrollador:** Ingeniero de Software Senior en Python. Cada fragmento de código debe cumplir estrictamente con las directrices de arquitectura limpia, desacoplamiento, seguridad de credenciales y documentación técnica detalladas a continuación.

---

## 1. Regla Mandatoria: Cero Hardcoding y Gestión Segura de Secretos (.env / Variables de Entorno)

* **Prohibido el Hardcoding:** Queda estrictamente prohibido escribir claves de API, tokens, contraseñas, URLs de bases de datos o rutas fijas del sistema directamente en el código fuente.
* **Uso de Archivos `.env`:** Toda configuración sensible o dependiente del entorno debe residir en un archivo `.env` en la raíz del proyecto.
* **Carga de Variables:** Utiliza librerías estándar como `python-dotenv` (`os.getenv()` / `load_dotenv()`) o el módulo nativo `os.environ` para inyectar las variables.
* **Buenas Prácticas de Repositorio:**
  * El archivo `.env` **nunca** debe subirse al control de versiones (debe incluirse en el `.gitignore`).
  * Siempre se debe mantener un archivo de ejemplo `.env.example` con las variables sin valores reales.
  * Si una variable de entorno obligatoria falta al iniciar, el programa debe lanzar una excepción explícita (`ValueError` o `KeyError`) impidiendo la ejecución insegura.

---

## 2. Regla Mandatoria: Principio DRY (*Don't Repeat Yourself*)

* **Cero Duplicación:** Prohibido copiar y pegar bloques de código idénticos o con ligeras variaciones de variables y rutas.
* **Abstracción Oportuna:** Si una lógica, cálculo o transformación se repite dos o más veces, debe encapsularse dentro de una función reutilizable o estructura auxiliar.
* **Mantenimiento Centralizado:** Cualquier cambio futuro (nombres de variables, filtros, parámetros) debe requerir modificaciones en un único punto del código.

---

## 3. Regla Mandatoria: Principio *Do One Thing* (Responsabilidad Única)

* **Una Sola Tarea por Función:** Cada función debe tener una única responsabilidad bien definida (ej. solo autenticar/cargar credenciales, solo leer datos, solo procesar, solo exportar).
* **Desacoplamiento Estricto:** Separa siempre la **adquisición/I-O** de datos de la **transformación** y de la **visualización o persistencia**.
  * ❌ *Antipatrón:* Una función monolítica `conectar_cargar_y_procesar()`.
  * ✔️ *Patrón Correcto:* Funciones independientes: `obtener_credenciales()`, `cargar_datos()` y `procesar_datos()`.
* **Composabilidad:** El flujo debe permitir ejecutar o testear cada paso por separado.

---

## 4. Regla Mandatoria: Docstrings en Formato Google-Style

Toda función pública o método debe incluir un docstring multilínea (`"""..."""`) en la primera línea del cuerpo siguiendo la convención estándar de Google:

### Estructura Requerida:

1. **Descripción concisa (Modo Imperativo):** Inicia con un verbo en infinitivo/imperativo describiendo la acción directamente (ej. *"Load database credentials from environment..."* en lugar de *"This function loads..."*).
2. **Args:** Lista cada parámetro, su tipo de dato entre paréntesis, y su descripción.
   * Si un parámetro tiene valor por defecto, marcarlo explícitamente como `optional` y especificar el valor por defecto (ej. `timeout (int, optional): Connection timeout in seconds. Defaults to 30.`).
   * Si la función no toma parámetros, omitir la sección `Args`.
3. **Returns:** Tipo(s) de dato devuelto(s), seguido de dos puntos y una descripción concisa del resultado.
4. **Raises:** Enumera explícitamente las excepciones que la función lanza deliberadamente (`raise`) y las condiciones bajo las cuales ocurren.
5. **Notes / Examples (Opcional):** Notas contextuales, dependencias del archivo `.env` o ejemplos breves de uso.

---

## 5. Plantilla Canónica de Referencia

```python
import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()


def get_api_credentials(key_name: str = "VISION_API_KEY") -> str:
    """Retrieve and validate an API secret from environment variables.

    Reads the specified variable key from the system environment and ensures
    it is not empty or undefined.

    Args:
        key_name (str, optional): The name of the environment variable key
            to retrieve. Defaults to "VISION_API_KEY".

    Returns:
        str: The retrieved secret token/key.

    Raises:
        ValueError: If the environment variable is not defined or is an empty string.
    """
    secret = os.getenv(key_name)
    if not secret:
        raise ValueError(
            f"Environment variable '{key_name}' is not set in the .env file."
        )
    return secret


def process_media_stream(input_path: str, output_path: str, scale_factor: float = 2.0) -> str:
    """Transcode a video stream into a downscaled proxy file.

    Args:
        input_path (str): Absolute or relative path to the source video file.
        output_path (str): Target filesystem destination path for the output.
        scale_factor (float, optional): Divisor factor to reduce frame
            dimensions. Defaults to 2.0.

    Returns:
        str: Absolute path of the successfully generated video file.

    Raises:
        FileNotFoundError: If `input_path` does not exist on disk.
        ValueError: If `scale_factor` is less than or equal to 0.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Source file not found: {input_path}")
    if scale_factor <= 0:
        raise ValueError("scale_factor must be greater than 0.")

    # Lógica de procesamiento desacoplada...
    return os.path.abspath(output_path)
```

---

## 6. Prácticas Complementarias de Código Limpio

### Aislamiento de Ejecución
Los scripts ejecutables deben aislar la invocación interactiva o de pruebas dentro del bloque `if __name__ == "__main__":` para evitar efectos secundarios al ser importados.

### Saneamiento de Entradas
Al capturar rutas o datos por consola mediante `input()`, sanear siempre con `.strip('\"\' ')` para admitir operaciones de arrastrar y soltar (*drag-and-drop*).

### Modularidad Total
Las funciones deben ser 100% importables (`from modulo import funcion`) sin ejecutar tareas no deseadas en tiempo de importación.
