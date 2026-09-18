# Skills de Páramo Urbano

Este directorio contiene los **Skills** de proyecto para el asistente de desarrollo Antigravity.

## Estructura esperada para cada Skill

Cada skill debe crearse dentro de una subcarpeta con su nombre y contener un archivo `SKILL.md` obligatorio con frontmatter YAML:

```text
.agents/skills/<nombre-del-skill>/
├── SKILL.md          # Requerido: Instrucciones principales con frontmatter YAML
├── scripts/          # Opcional: Scripts y herramientas ejecutables
├── examples/         # Opcional: Ejemplos de referencia
├── resources/        # Opcional: Plantillas o recursos adicionales
└── references/       # Opcional: Documentación detallada de consulta
```

## Ejemplo de `SKILL.md`

```markdown
---
name: mi-skill-especializado
description: >-
  Describe cuándo el agente debe activar este skill.
  Ejemplo: "Utiliza este skill al realizar tareas de cálculo biomecánico o pruebas de ingesta de archivos .FIT."
---

# Mi Skill Especializado

Instrucciones y procedimientos paso a paso para el agente...
```
