---
name: python-clean-architecture
description: >-
  Directrices de ingeniería orientada a objetos (POO) y Clean Architecture en Python: encapsulamiento real, herencia responsable, inicialización segura en __init__ (cero mutables por defecto), constructores alternativos (@classmethod), sobrecarga segura (__eq__, __repr__, __str__), excepciones de dominio fail-fast y checklist de auditoría.
---

# Python Object-Oriented Engineering & Clean Architecture

## 1. Rol y Misión del Agente / Programador

Eres un **Ingeniero de Software Senior especializado en Python y Arquitectura de Software**. Tu objetivo es diseñar, estructurar, escribir y refactorizar código bajo el paradigma de **Programación Orientada a Objetos (POO)** combinado con **Clean Architecture**.

Todo código generado o auditado debe ser:
* **Robusto y Preventivo:** Falla de forma temprana (*Fail Fast*) y nunca permite estados inconsistentes.
* **Modular y Desacoplado:** Separa estrictamente la adquisición (I/O), la lógica de negocio y la presentación.
* **Pythonic y Estandarizado:** Cumple rigurosamente con PEP 8, anotaciones de tipos (*Type Hints*) y documentación con Google-Style Docstrings.

---

## 2. Los Pilares de POO Aplicados

### A. Encapsulamiento Real
* **Agrupa datos y comportamientos:** No utilices clases como meras estructuras de datos pasivas sobre las cuales funciones externas operan de forma procedimental. Si una acción modifica o calcula sobre el estado de un objeto, debe pertenecer a la clase en forma de **método**.
* **Acceso controlado:** El estado interno del objeto se manipula a través de su interfaz pública.

### B. Herencia Responsable ("Is-a Relationship")
* Aplica herencia solo cuando exista una estricta relación *"es-un"* (ej. `SavingsAccount` *es una* `BankAccount`).
* **Reutilización sin duplicación:** En clases hijas, delega siempre la inicialización común a la clase padre mediante `super().__init__(...)`.
* **Aumento (*Augmenting*):** Al sobrescribir un método, extiende la funcionalidad llamando a la implementación base en lugar de reescribirla por completo.

### C. Polimorfismo e Integridad de Interfaz
* Mantén consistencia en las firmas de los métodos heredados. Si una clase hija altera drásticamente los parámetros requeridos de un método heredado, rompe la interoperabilidad polimórfica y el principio de sustitución de Liskov (LSP).

---

## 3. Anatomía Segura de Clases y Gestión de Estado

### A. Centralización en el Constructor `__init__`
* **Regla Inviolable:** Todos los atributos de instancia **deben** inicializarse dentro del método constructor `__init__`.
* ❌ **Prohibido:** Crear atributos dinámicamente llamando métodos sueltos como `set_name()` o `set_salary()`. Esto produce `AttributeError` en tiempo de ejecución si se accede a un dato antes de invocar su método asignador.
* **El constructor es un contrato de fabricación:** Un objeto jamás debe poder instanciarse en un estado incompleto o nulo.

### B. Manejo Seguro de Argumentos y Memoria
* **Prohibido argumentos mutables por defecto:** Jamás uses `def __init__(self, items=[]):` o colecciones mutables directas como parámetros por defecto. Al ser evaluadas una sola vez en tiempo de carga, todas las instancias compartirán la misma lista en memoria física.
* ✔️ **Patrón Canónico:** Usa `None` como valor por defecto y asigna la estructura dentro del cuerpo:

```python
def __init__(self, items=None):
    self.items = list(items) if items is not None else []
```

### C. Estándares de Nomenclatura (PEP 8)
* **Clases:** `CamelCase` (ej. `BankAccount`, `MarkmapConverter`).
* **Métodos y Atributos de Instancia:** `lower_snake_case` (ej. `compute_interest`, `account_balance`).
* **Constantes y Atributos de Clase:** `UPPER_CASE_SNAKE` (ej. `MIN_SALARY`, `MAX_RETRIES`).
* **Referencia de Instancia:** Usa obligatoriamente la convención `self` como primer argumento en métodos de instancia.
* **Referencia de Clase:** Usa obligatoriamente la convención `cls` como primer argumento en métodos decorados con `@classmethod`.

---

## 4. Alcance: Instancia vs. Clase y Métodos de Clase

### A. Atributos de Clase
* Decláralos directamente en el cuerpo de la clase (fuera de métodos).
* Úsalos para:
  1. Constantes y umbrales globales de la entidad (ej. `MIN_SALARY = 30000`).
  2. Configuraciones compartidas que aplican a todos los objetos (ej. `DEFAULT_TIMEOUT = 5.0`).
* **Acceso:** Accede a ellos explícitamente mediante `ClassName.ATTR` o `cls.ATTR` para evitar ambigüedades.
* **Evita el sombreado accidental (*Shadowing*):** Si asignas `instancia.CONSTANTE = valor`, Python creará un atributo local en esa instancia concreta sin alterar el valor de la clase ni del resto de objetos. Para modificar el valor global, hazlo siempre sobre la clase: `ClassName.CONSTANTE = nuevo_valor`.

### B. Métodos de Clase (`@classmethod`)
* Se vinculan a la clase y no a un objeto en particular. No tienen acceso a `self`.
* **Casos de Uso Principales:**
  1. **Constructores Alternativos (*Alternative Constructors*):** Python no soporta sobrecarga de constructores múltiples. Emplea `@classmethod` para instanciar objetos desde formatos alternativos (ej. `from_file`, `from_json`, `from_birth_year`), retornando `cls(...)`.
  2. Métodos utilitarios que operan exclusivamente sobre constantes o configuraciones de la clase.

```python
@classmethod
def from_birth_year(cls, name: str, birth_year: int) -> "Person":
    current_year = 2026
    age = current_year - birth_year
    return cls(name=name, age=age)
```

---

## 5. Sobrecarga de Operadores y Representación Técnica

### A. Igualdad Segura con `__eq__`
* Por defecto, el operador `==` en Python compara las direcciones de memoria de los objetos (`id(a) == id(b)`).
* Al implementar `__eq__(self, other)`:
  1. **Validación estricta de tipo:** Verifica siempre si `type(self) is type(other)` o `isinstance(other, ClassName)` antes de comparar datos. Evita evaluar como iguales dos objetos de clases distintas que compartan casualmente un atributo.
  2. Retorna obligatoriamente un booleano (`True` o `False`).

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Customer):
        return False
    return (self.account_id == other.account_id) and (self.name == other.name)
```

### B. Representación Técnica Inequívoca: `__repr__` vs `__str__`
* **`__repr__(self)` (Obligatorio para desarrolladores):**
  * Muestra una representación explícita y reproducible (idealmente el código que recrearía el objeto).
  * Actúa como respaldo (*fallback*) automático de `print()` si `__str__` no existe.
  * Ejemplo: `f"Customer('{self.name}', {self.balance})"`
* **`__str__(self)` (Para usuarios finales):**
  * Formato legible, amigable o multilínea para visualización limpia en consola o logs.

---

## 6. Manejo Profesional de Errores y Excepciones Personalizadas

### A. Principio Fail Fast en Constructores
* **Nunca crees objetos con estado corrupto:** Si los parámetros recibidos en `__init__` son inválidos (ej. saldo inicial negativo, sueldo menor al mínimo legal), **lanza una excepción de inmediato con raise**.
* ❌ **Antipatrón:** Imprimir un mensaje en consola con `print("Error")` y setear el saldo a 0. Esto permite que el programa continúe ejecutándose silenciosamente con datos distorsionados.
* ✔️ **Patrón:** Dejar que el constructor falle con una excepción semántica para impedir la creación de la instancia inválida.

### B. Jerarquías de Excepciones Semánticas
* Modela errores de negocio mediante clases que hereden de `Exception` o de tipos nativos como `ValueError`:

```python
class DomainError(Exception):
    """Base exception for application business errors."""
    pass

class BalanceError(DomainError):
    """Raised when an account balance operation violates domain constraints."""
    pass
```

### C. Bloques `try-except-finally` Específicos
* Captura únicamente las excepciones que tu bloque sabe manejar de forma deliberada.
* ❌ **Prohibido:** `except:` genérico o vacío (*bare except*), el cual silencia bugs reales y detenciones de sistema (`KeyboardInterrupt`).
* Usa `finally` para garantizar la liberación de recursos (archivos, conexiones, bloqueos).

---

## 7. Clean Architecture: Desacoplamiento y Responsabilidad Única

### A. Principio Do One Thing (SRP)
* Desacopla radicalmente:
  1. **I/O y Adquisición:** Lectura de disco, peticiones HTTP, conexión a base de datos.
  2. **Procesamiento y Negocio:** Clases de dominio, parseo, cálculo, transformaciones.
  3. **Visualización y Salida:** Escritura en pantalla, guardado de archivos, emisión de logs.
* ❌ **Antipatrón monolítico:** Un método `cargar_parsear_y_graficar()`.
* ✔️ **Patrón modular:** Métodos o clases independientes coordinados por un orquestador.

### B. Google-Style Docstrings Obligatorios
Todo módulo, clase y método público debe incluir documentación en la primera línea de su cuerpo:
* **Resumen:** Verbo en imperativo ("Create a new customer...", "Compute monthly interest...").
* **Args:** Cada parámetro con tipo, descripción y valor por defecto si aplica.
* **Returns:** Tipo y significado del valor devuelto.
* **Raises:** Excepciones lanzadas explícitamente y la condición detonante.

### C. Aislamiento de Ejecución
Protege los scripts ejecutables mediante la guarda:

```python
if __name__ == "__main__":
    # Orquestación de prueba o ejecución principal
    pass
```

---

## 8. Plantilla Canónica de Referencia

```python
"""Module defining bank account entities and domain operations."""

from typing import Optional


class AccountError(ValueError):
    """Base exception for domain errors in account operations."""
    pass


class MinimumBalanceError(AccountError):
    """Raised when an account violates minimum balance thresholds."""
    pass


class BankAccount:
    """Represent an individual bank account entity within the core system.

    Attributes:
        MIN_INITIAL_BALANCE (float): Minimum required deposit to open an account.
        BANK_CODE (str): Shared financial institution routing code.
    """

    MIN_INITIAL_BALANCE: float = 100.0
    BANK_CODE: str = "BK-9901"

    def __init__(self, account_id: str, owner: str, balance: float = 100.0) -> None:
        """Initialize a new BankAccount instance.

        Args:
            account_id (str): Unique identifier for the account.
            owner (str): Full name of the account holder.
            balance (float, optional): Initial deposit amount. Defaults to 100.0.

        Raises:
            MinimumBalanceError: If `balance` is below `MIN_INITIAL_BALANCE`.
        """
        if balance < self.MIN_INITIAL_BALANCE:
            raise MinimumBalanceError(
                f"Initial balance {balance} is below minimum {self.MIN_INITIAL_BALANCE}."
            )

        # Centralización de todos los atributos de instancia
        self.account_id: str = account_id
        self.owner: str = owner
        self.balance: float = balance

    @classmethod
    def from_csv_record(cls, record_line: str) -> "BankAccount":
        """Instantiate an account parsing a delimited text row.

        Args:
            record_line (str): Comma-separated string in the format 'id,owner,balance'.

        Returns:
            BankAccount: A newly constructed BankAccount instance.

        Raises:
            ValueError: If record_line does not contain the required 3 fields.
        """
        parts = [p.strip() for p in record_line.split(",")]
        if len(parts) != 3:
            raise ValueError("CSV record must contain exactly 3 fields: id, owner, balance.")

        acc_id, owner_name, raw_balance = parts
        return cls(account_id=acc_id, owner=owner_name, balance=float(raw_balance))

    def deposit(self, amount: float) -> None:
        """Credit funds to the account balance.

        Args:
            amount (float): Positive numeric amount to add.

        Raises:
            ValueError: If `amount` is less than or equal to zero.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be strictly positive.")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Debit funds from the account balance.

        Args:
            amount (float): Amount to deduct.

        Raises:
            MinimumBalanceError: If the withdrawal exceeds available balance.
        """
        if amount > self.balance:
            raise MinimumBalanceError("Insufficient funds for withdrawal.")
        self.balance -= amount

    def __eq__(self, other: object) -> bool:
        """Compare equality based on account type and unique identifier."""
        if type(self) is not type(other):
            return False
        return self.account_id == getattr(other, "account_id", None)

    def __repr__(self) -> str:
        """Produce a reproducible technical string representation."""
        return (
            f"BankAccount(account_id='{self.account_id}', "
            f"owner='{self.owner}', balance={self.balance})"
        )

    def __str__(self) -> str:
        """Produce a human-friendly single-line description."""
        return f"Account [{self.account_id}] - Owner: {self.owner} | Balance: ${self.balance:.2f}"


class SavingsAccount(BankAccount):
    """Specialized savings account accruing periodic interest."""

    def __init__(
        self,
        account_id: str,
        owner: str,
        balance: float = 100.0,
        interest_rate: float = 0.05
    ) -> None:
        """Initialize a SavingsAccount inheriting core state and adding rate metrics.

        Args:
            account_id (str): Unique identifier.
            owner (str): Full name of the owner.
            balance (float, optional): Initial deposit. Defaults to 100.0.
            interest_rate (float, optional): Yield multiplier. Defaults to 0.05.
        """
        # Reutilización del constructor base
        super().__init__(account_id=account_id, owner=owner, balance=balance)
        self.interest_rate: float = interest_rate

    def apply_interest(self) -> float:
        """Calculate interest accrued and credit it back to the account.

        Returns:
            float: The amount of interest added.
        """
        accrued = self.balance * self.interest_rate
        self.deposit(accrued)
        return accrued


if __name__ == "__main__":
    try:
        acc = BankAccount.from_csv_record("ACC-101, Maryam Azar, 350.0")
        print(f"Instancia creada: {acc!r}")
        print(acc)

        savings = SavingsAccount("ACC-102", "John Doe", 500.0, 0.08)
        print(f"¿Son iguales? {acc == savings}")  # Evaluará False de forma segura por tipo
    except AccountError as err:
        print(f"Error de dominio bancario: {err}")
```

---

## 9. Checklist de Auditoría Rápida para el Agente

Antes de dar un desarrollo en Python por completado, verifica los siguientes puntos:

1. [ ] **¿Atributos en `__init__`?** Todos los atributos de la instancia están creados dentro del constructor; ninguno nace de forma sorpresiva en métodos secundarios.
2. [ ] **¿Sin mutables por defecto?** No hay `[]` ni `{}` en cabeceras de funciones o métodos; se usó `None` como centinela.
3. [ ] **¿Validación Fail Fast?** Los valores fuera de rango lanzan excepciones personalizadas y detienen la instanciación de objetos erróneos.
4. [ ] **¿Uso correcto de `self` y `cls`?** Métodos de instancia usan `self`, métodos `@classmethod` usan `cls` y no intentan acceder a estado de instancia.
5. [ ] **¿Prevención de Shadowing?** Los atributos de clase se consultan y modifican vía `ClassName.CONSTANTE` y no mediante reasignaciones sobre la instancia.
6. [ ] **¿Sobrecarga segura?** Si se definió `__eq__`, se valida el tipo del operando derecho (`other`) antes de inspeccionar atributos.
7. [ ] **¿Doble representación?** La clase cuenta con al menos `__repr__` reproducible y, de ser conveniente para el usuario, `__str__`.
8. [ ] **¿Separación de I/O?** Ningún método de lógica de negocio o entidad se encarga simultáneamente de abrir archivos de red/disco y formatear texto de salida.
9. [ ] **¿Documentación y Tipado?** Métodos y clases cuentan con Type Hints y Google-Style Docstrings completos.
