---
name: python-enterprise-oop
description: >-
  Patrones avanzados y POO empresarial en Python: tipado estricto (type hints), descriptores con @property (getter, setter, deleter), intercepción (__getattr__, __setattr__ con __dict__), resolución MRO en herencia múltiple, sobrecarga semántica de operadores, protocolo de iteradores (__iter__, __next__), interfaces formales/ABCs (@abstractmethod) y Factory Method.
---

# Enterprise Object-Oriented Programming in Python (Intermediate OOP)

## 1. Identidad y Propósito del Skill

Este skill define el conjunto de reglas, directrices de arquitectura y mejores prácticas para diseñar y escribir código Python profesional (*enterprise-grade*), desacoplado, modular y escalable.

Cualquier agente o desarrollador que active este skill debe adherirse estrictamente a los lineamientos de tipado estricto, encapsulamiento mediante descriptores, herencia controlada con MRO, sobrecarga idiomática de operadores, protocolo de iteradores, contratos formales (ABCs/Interfaces) y patrones creacionales (Factory Method).

---

## 2. Los 7 Mandamientos de Calidad de Código

1. **Tipado Obligatorio (*Enterprise-Grade Typing*):** Todo atributo, parámetro y retorno de método debe tener *type hints* explícitos. Si un método no retorna nada, debe declararse explícitamente `-> None`.
2. **Contratos Explícitos:** Toda clase base compartida debe heredar de `abc.ABC` y definir sus métodos abstractos con `@abstractmethod`. No uses interfaces implícitas si requieres cumplimiento en tiempo de ejecución.
3. **Encapsulamiento con Propiedades:** Nunca expongas mutaciones directas de datos sensibles o que requieran validación; utiliza el decorador `@property` junto con sus variantes `.setter` y `.deleter`, almacenando el estado en variables internas prefijadas con guion bajo (`self._attribute`).
4. **Respeto al MRO y C3:** Al modelar herencia múltiple y multinivel, verifica el orden de precedencia local y llama siempre a los constructores correspondientes utilizando `super().__init__(...)` o la delegación explícita adecuada sin romper la cadena.
5. **Sobrecarga Idiomática:** Implementa métodos dunder (`__eq__`, `__add__`, etc.) para otorgar naturalidad matemática y semántica a las entidades del dominio, garantizando que retornen nuevas instancias cuando aplique.
6. **Iteración Segura:** Todo generador o flujo de datos personalizado debe cumplir formalmente el protocolo de iterador (`__iter__` y `__next__`), asegurando siempre el lanzamiento de `StopIteration` para evitar bucles infinitos.
7. **Desacoplamiento Creacional:** Evita cadenas de `if/elif/else` acopladas a la instanciación de clases concretas dentro de métodos de negocio; abstrae la creación usando el patrón *Factory Method* prefijado por convención con `_`.

---

## 3. Guía Operativa y Patrones de Implementación

### Regla 1: Tipado Estático y Modelado de Tipos
* **Uso:** Utiliza tipos nativos (`int`, `str`, `float`, `bool`) y el módulo `typing` (`List`, `Dict`, `Tuple`, `Optional`, `Callable`, `Iterator`, `Any`).
* **Clases Propias:** Utiliza los nombres de clases existentes como tipos válidos para documentar y restringir entradas/salidas.

```python
from typing import List, Dict, Optional


class Course:
    def __init__(self, course_code: str, credits: int) -> None:
        self.course_code: str = course_code
        self.credits: int = credits


class Student:
    def __init__(self, name: str, student_id: int, tuition_balance: float) -> None:
        self.name: str = name
        self.student_id: int = student_id
        self.tuition_balance: float = tuition_balance
        self.courses: List[Course] = []

    def enroll(self, course: Course) -> None:
        self.courses.append(course)

    def get_schedule(self) -> Dict[str, int]:
        return {c.course_code: c.credits for c in self.courses}
```

### Regla 2: Descriptores y Encapsulamiento con `@property`
* **Getter:** `@property` para transformar, formatear o enmascarar la lectura.
* **Setter:** `@<attr>.setter` para validar tipos, formatos o rangos antes de guardar en `self._<attr>`.
* **Deleter:** `@<attr>.deleter` para prevenir borrados no autorizados (`raise AttributeError`) o limpiar recursos.

```python
class SensitiveRecord:
    def __init__(self, identifier: str, ssn: str) -> None:
        self.identifier: str = identifier
        self.ssn: str = ssn  # Invoca el setter automáticamente

    @property
    def ssn(self) -> str:
        """Devuelve el SSN ofuscado mostrando únicamente los últimos 4 dígitos."""
        return f"XXX-XX-{self._ssn[-4:]}"

    @ssn.setter
    def ssn(self, new_ssn: str) -> None:
        if not isinstance(new_ssn, str) or len(new_ssn) != 11:
            raise ValueError("El SSN debe tener un formato válido de 11 caracteres (XXX-XX-XXXX).")
        self._ssn: str = new_ssn

    @ssn.deleter
    def ssn(self) -> None:
        raise AttributeError("Operación denegada: No está permitido eliminar el atributo SSN.")
```

### Regla 3: Intercepción Dinámica de Atributos (`__getattr__` y `__setattr__`)
* `__getattr__(self, name)`: Se ejecuta **únicamente** cuando se intenta acceder a un atributo que **no existe** en el *namespace* del objeto. Sirve para placeholders o valores dinámicos por defecto.
* `__setattr__(self, name, value)`: Intercepta **todas** las asignaciones de atributos.
* **Peligro Crítico:** Dentro de `__setattr__`, **nunca** uses `self.name = value` (generaría recursión infinita). Usa siempre `self.__dict__[name] = value`.

```python
from typing import Any


class DynamicEntity:
    def __init__(self, entity_type: str) -> None:
        self.__dict__["entity_type"] = entity_type

    def __getattr__(self, name: str) -> Any:
        # Crea un placeholder en lugar de lanzar AttributeError
        self.__setattr__(name, None)
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        # Validación global o transformación
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise TypeError(f"El valor asignado a '{name}' debe ser de tipo primitivo.")
        self.__dict__[name] = value
```

### Regla 4: Herencia Múltiple, Multinivel y Orden de Resolución (MRO)
* Modela relaciones estrictas de identidad ("es-un").
* Respeta el algoritmo de linealización C3:
  1. Las clases hijas se evalúan antes que las clases padre.
  2. Los padres se evalúan de izquierda a derecha según la declaración en la firma: `class Child(ParentA, ParentB)`.
* Consulta el MRO cuando depures colisiones de métodos usando `Clase.mro()` o `Clase.__mro__`.

```python
from typing import Any


class Employee:
    def __init__(self, employee_id: str, department: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.employee_id: str = employee_id
        self.department: str = department

    def introduce(self) -> str:
        return f"Empleado ID: {self.employee_id} ({self.department})"


class Student:
    def __init__(self, university: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.university: str = university

    def introduce(self) -> str:
        return f"Estudiante de {self.university}"


# Herencia múltiple: Employee tiene precedencia sobre Student en MRO
class Intern(Employee, Student):
    def __init__(self, employee_id: str, department: str, university: str, mentor: str) -> None:
        super().__init__(employee_id=employee_id, department=department, university=university)
        self.mentor: str = mentor

    def introduce(self) -> str:
        # Sobrescritura personalizada extendiendo la funcionalidad
        parent_intro = super().introduce()
        return f"{parent_intro}, mentor asignado: {self.mentor}"
```

### Regla 5: Sobrecarga de Operadores (Magic Methods)
* Implementa métodos mágicos para dotar de semántica natural a los objetos de dominio.
* `__eq__(self, other)`: Compara por atributos de estado, asegurando tipado booleano de retorno.
* `__add__(self, other)`: Puede fusionar colecciones homogéneas o generar una nueva abstracción compuesta (p. ej., `Developer + Developer -> Team`).

```python
from typing import Any, List


class Team:
    def __init__(self, members: List[str]) -> None:
        self.members: List[str] = members

    def __add__(self, other: "Team") -> "Team":
        if not isinstance(other, Team):
            raise TypeError("Solo se pueden sumar instancias de tipo Team.")
        return Team(self.members + other.members)


class Developer:
    def __init__(self, name: str, role: str) -> None:
        self.name: str = name
        self.role: str = role

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Developer):
            return False
        return self.name == other.name and self.role == other.role

    def __add__(self, other: "Developer") -> Team:
        if not isinstance(other, Developer):
            raise TypeError("Un Developer solo puede unirse con otro Developer para formar un Team.")
        return Team([self.name, other.name])
```

### Regla 6: Protocolo de Iteradores Personalizados
Para crear una secuencia eficiente o generador de datos bajo demanda:
1. `__iter__(self) -> self`: Retorna la referencia del iterador.
2. `__next__(self)`: Incrementa el estado o genera el siguiente ítem. Cuando la condición de fin se cumple, debe disparar obligatoriamente `raise StopIteration`.

```python
from typing import Tuple


class BatchProcessor:
    def __init__(self, total_items: int, batch_size: int) -> None:
        self.total_items: int = total_items
        self.batch_size: int = batch_size
        self._current_index: int = 0

    def __iter__(self) -> "BatchProcessor":
        return self

    def __next__(self) -> Tuple[int, int]:
        if self._current_index >= self.total_items:
            raise StopIteration
        start = self._current_index
        end = min(self._current_index + self.batch_size, self.total_items)
        self._current_index = end
        return (start, end)
```

### Regla 7: Clases Base Abstractas (ABCs) vs. Interfaces Formales
* **Clase Base Abstracta (ABC - "is-a"):** Actúa como plantilla. Puede combinar métodos abstractos (`@abstractmethod`) con métodos concretos ya implementados que heredarán todas las subclases.
* **Interfaz Formal ("must-do"):** Define un contrato puro. Hereda de `ABC` y **únicamente** contiene métodos decorados con `@abstractmethod` que contienen `pass`. Ninguna subclase puede instanciarse sin definir todos sus métodos.

```python
from abc import ABC, abstractmethod


# Interfaz Formal: Contrato estricto
class Notifier(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        """Contrato formal: todos los notificadores deben implementar send."""
        pass


# Implementación concreta del contrato
class EmailNotifier(Notifier):
    def send(self, recipient: str, message: str) -> bool:
        print(f"Enviando correo a {recipient}: {message}")
        return True
```

### Regla 8: Patrón de Diseño Factory Method
* **Problema:** Métodos sobrecargados con bifurcaciones `if/elif/else` que instancian clases directamente.
* **Solución:** Aislar la instanciación en un método de fábrica (convención `_create_<entidad>`), retornando objetos que compartan una misma Interfaz/ABC (el *Product*).

```python
from abc import ABC, abstractmethod
from typing import Dict, Any


# Producto (Interfaz)
class ReportGenerator(ABC):
    @abstractmethod
    def build_report(self, data: Dict[str, Any]) -> str:
        pass


# Productos Concretos
class PDFReport(ReportGenerator):
    def build_report(self, data: Dict[str, Any]) -> str:
        return f"[PDF Format] Reporte con {len(data)} registros."


class CSVReport(ReportGenerator):
    def build_report(self, data: Dict[str, Any]) -> str:
        return f"[CSV Format] Reporte con {len(data)} registros."


# Cliente desacoplado con Factory Method
class AnalyticsService:
    def _create_report_generator(self, format_type: str) -> ReportGenerator:
        """Factory Method para instanciar el generador según el formato requerido."""
        format_lower = format_type.lower()
        if format_lower == "pdf":
            return PDFReport()
        elif format_lower == "csv":
            return CSVReport()
        raise ValueError(f"Formato no soportado: {format_type}")

    def generate(self, format_type: str, dataset: Dict[str, Any]) -> str:
        # El método de negocio desconoce la clase concreta; solo depende de la interfaz
        generator: ReportGenerator = self._create_report_generator(format_type)
        return generator.build_report(dataset)
```

---

## 4. Matriz de Autoevaluación para Agentes y Desarrolladores

Antes de entregar código producido bajo este skill, valida cada uno de los siguientes puntos:

| Criterio | Pregunta de Control | Estado Requerido |
| :--- | :--- | :--- |
| **Type Hints** | ¿Todos los parámetros y retornos tienen anotación (`def m(self, x: int) -> None:`)? | **SÍ** |
| **Encapsulamiento** | ¿Los atributos críticos usan `@property` y `self._variable`? | **SÍ** |
| **Recursión en `__setattr__`** | Si se usa `__setattr__`, ¿se muta a través de `self.__dict__` para evitar recursión? | **SÍ** |
| **MRO / Jerarquía** | En herencia múltiple, ¿el orden de clases en la firma respeta la prioridad de resolución? | **SÍ** |
| **Dunder Methods** | ¿Los métodos mágicos (`__eq__`, `__add__`) validan el tipo del operando `other`? | **SÍ** |
| **Iteradores** | ¿La clase iterador implementa tanto `__iter__` como `__next__` y lanza `StopIteration`? | **SÍ** |
| **ABCs e Interfaces** | ¿Las clases abstractas heredan de `ABC` y usan `@abstractmethod` sin implementar lógica de contrato? | **SÍ** |
| **Factory Method** | ¿Se separó la lógica de creación de instancias de la lógica de procesamiento principal? | **SÍ** |
