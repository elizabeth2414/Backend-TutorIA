# 🎮 Sistema de Gamificación TutorIA

Documentación completa del sistema de puntos, niveles y recompensas.

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Arquitectura](#arquitectura)
3. [Sistema de Puntos](#sistema-de-puntos)
4. [Sistema de Niveles](#sistema-de-niveles)
5. [Recompensas](#recompensas)
6. [Misiones Diarias](#misiones-diarias)
7. [Casos de Uso](#casos-de-uso)
8. [Unificación de Lógica](#unificación-de-lógica)
9. [API Reference](#api-reference)

---

## 🎯 Introducción

El sistema de gamificación de TutorIA motiva a los estudiantes mediante:

- **Puntos (XP)**: Se ganan completando lecturas, actividades, ejercicios
- **Niveles**: Los estudiantes suben de nivel al acumular puntos
- **Recompensas**: Badges, avatares, títulos desbloqueables
- **Misiones Diarias**: Objetivos diarios con recompensas
- **Rachas**: Días consecutivos de práctica

---

## 🏗️ Arquitectura

### Modelos de Datos

```
estudiante (1) ←→ (1) nivel_estudiante
    ↓
    ↓ (N)
historial_puntos

estudiante (1) ←→ (N) recompensa_estudiante ←→ (N) recompensa
estudiante (1) ←→ (N) mision_diaria
```

### Tablas Principales

#### `nivel_estudiante`
```sql
id                          BIGSERIAL PRIMARY KEY
estudiante_id               BIGINT (FK → estudiante.id)
nivel_actual                INTEGER (default 1)
puntos_totales              INTEGER (default 0)
puntos_nivel_actual         INTEGER (default 0)  -- XP en el nivel actual
puntos_para_siguiente_nivel INTEGER (default 1000)
lecturas_completadas        INTEGER (default 0)
actividades_completadas     INTEGER (default 0)
racha_actual                INTEGER (default 0)
racha_maxima                INTEGER (default 0)
```

#### `historial_puntos`
```sql
id            BIGSERIAL PRIMARY KEY
estudiante_id BIGINT (FK → estudiante.id)
motivo        VARCHAR(200)
puntos        INTEGER
fecha         TIMESTAMP (default NOW())
```

---

## 💎 Sistema de Puntos

### ⚠️ IMPORTANTE: Unificación de Lógica

**❌ ANTES (Duplicación)**:
- Función PostgreSQL `agregar_puntos_estudiante()`
- Función Python `agregar_puntos_estudiante()`
- **Problema**: Lógica duplicada, difícil de mantener

**✅ AHORA (Unificado)**:
- **ÚNICA** función Python `app.servicios.gamificacion.agregar_puntos_estudiante()`
- Función PostgreSQL **DEPRECATED** (ver `migrations/deprecar_funcion_agregar_puntos.sql`)

### Cómo Agregar Puntos

**Siempre usa la función Python:**

```python
from app.servicios.gamificacion import agregar_puntos_estudiante
from app.esquemas.gamificacion import HistorialPuntosCreate

# Crear registro de puntos
puntos = HistorialPuntosCreate(
    estudiante_id=1,
    puntos=100,
    motivo="Completó lectura 'El Principito'"
)

# Agregar puntos (actualiza nivel automáticamente)
resultado = agregar_puntos_estudiante(db, puntos)
```

**Desde un endpoint:**

```python
POST /gamificacion/puntos
{
  "estudiante_id": 1,
  "puntos": 100,
  "motivo": "Completó lectura 'El Principito'"
}
```

### Qué Hace Automáticamente

La función `agregar_puntos_estudiante()` maneja:

1. ✅ **Validaciones**:
   - Verifica que el estudiante existe
   - Valida puntos no negativos (permite negativos explícitos para penalizaciones)

2. ✅ **Registro en historial**:
   - Guarda en `historial_puntos` con motivo y fecha

3. ✅ **Creación automática de nivel**:
   - Si el estudiante no tiene `nivel_estudiante`, lo crea automáticamente

4. ✅ **Actualización de puntos**:
   - Incrementa `puntos_totales` (nunca decrece, es acumulativo)
   - Incrementa `puntos_nivel_actual` (XP en el nivel actual)

5. ✅ **Subida de nivel automática**:
   - Cuando `puntos_nivel_actual >= puntos_para_siguiente_nivel`:
     - Sube de nivel
     - Resetea XP del nivel (restando lo necesario)
     - Calcula puntos para el siguiente nivel
   - **Puede subir múltiples niveles** si ganó muchos puntos

6. ✅ **Logging detallado**:
   - Log de puntos agregados
   - Log de nivel creado (si no existía)
   - Log de subida de nivel (con emoji 🎉)
   - Log de progreso hacia el siguiente nivel

---

## 📊 Sistema de Niveles

### Fórmula de Niveles

```
Puntos necesarios = nivel_actual * 1000

Nivel 1: 0 → 1000 pts
Nivel 2: 1000 → 2000 pts
Nivel 3: 2000 → 3000 pts
...
Nivel N: (N-1)*1000 → N*1000 pts
```

### Ejemplos de Progresión

**Ejemplo 1: Subida de un solo nivel**
```python
# Estado inicial
nivel_actual = 1
puntos_nivel_actual = 850
puntos_para_siguiente_nivel = 1000

# Agregar 200 puntos
agregar_puntos_estudiante(db, HistorialPuntosCreate(
    estudiante_id=1,
    puntos=200,
    motivo="Completó actividad"
))

# Estado final
nivel_actual = 2  # ¡Subió!
puntos_nivel_actual = 50  # 850 + 200 - 1000
puntos_para_siguiente_nivel = 2000  # 2 * 1000
puntos_totales = 1050  # Acumulativo
```

**Ejemplo 2: Subida de múltiples niveles**
```python
# Estado inicial
nivel_actual = 1
puntos_nivel_actual = 500
puntos_para_siguiente_nivel = 1000

# Agregar 5000 puntos (¡premio especial!)
agregar_puntos_estudiante(db, HistorialPuntosCreate(
    estudiante_id=1,
    puntos=5000,
    motivo="¡Premio especial por racha de 30 días!"
))

# Estado final
nivel_actual = 4  # ¡Subió 3 niveles!
puntos_nivel_actual = 500  # 500 + 5000 - 1000 - 2000 - 3000
puntos_para_siguiente_nivel = 4000  # 4 * 1000
puntos_totales = 5500  # Acumulativo
```

### Consultar Nivel de un Estudiante

```python
GET /gamificacion/estudiante/{estudiante_id}/progreso

Response:
{
  "id": 1,
  "nombre": "Juan Pérez",
  "nivel_actual": 3,
  "xp_actual": 1500,
  "xp_para_siguiente_nivel": 3000,
  "racha_actual": 5
}
```

---

## 🏆 Recompensas

Las recompensas son badges, avatares o títulos que los estudiantes pueden desbloquear.

### Estructura

```python
# Modelo Recompensa
{
  "id": 1,
  "nombre": "Lector Principiante",
  "descripcion": "Completó su primera lectura",
  "tipo": "badge",  # badge, avatar, titulo
  "imagen_url": "/badges/lector_principiante.png",
  "puntos_requeridos": 100,
  "activo": true
}
```

### Asignar Recompensa a Estudiante

```python
POST /gamificacion/recompensas/estudiante
{
  "estudiante_id": 1,
  "recompensa_id": 5
}
```

### Listar Recompensas de un Estudiante

```python
GET /gamificacion/estudiante/{estudiante_id}/recompensas

Response:
[
  {
    "id": 1,
    "estudiante_id": 1,
    "recompensa_id": 5,
    "fecha_obtencion": "2025-12-27T10:30:00",
    "recompensa": {
      "nombre": "Lector Principiante",
      "tipo": "badge",
      ...
    }
  }
]
```

---

## 📅 Misiones Diarias

Objetivos diarios que los estudiantes pueden completar para ganar puntos extra.

### Estructura

```python
{
  "id": 1,
  "estudiante_id": 1,
  "descripcion": "Lee 3 textos hoy",
  "objetivo": 3,
  "progreso": 1,
  "completada": false,
  "puntos_recompensa": 50,
  "fecha": "2025-12-27"
}
```

### Crear Misión Diaria

```python
POST /gamificacion/misiones
{
  "estudiante_id": 1,
  "descripcion": "Lee 3 textos hoy",
  "objetivo": 3,
  "puntos_recompensa": 50,
  "fecha": "2025-12-27"
}
```

### Actualizar Progreso

```python
PUT /gamificacion/misiones/{mision_id}/progreso?progreso=2
```

Cuando `progreso >= objetivo`, la misión se marca como `completada = true` automáticamente.

---

## 📝 Casos de Uso

### Caso 1: Estudiante Completa una Lectura

```python
from app.servicios.gamificacion import agregar_puntos_estudiante
from app.esquemas.gamificacion import HistorialPuntosCreate

def completar_lectura(db: Session, estudiante_id: int, lectura_id: int):
    # 1. Marcar lectura como completada
    # ... lógica de lectura ...

    # 2. Agregar puntos
    agregar_puntos_estudiante(db, HistorialPuntosCreate(
        estudiante_id=estudiante_id,
        puntos=150,
        motivo=f"Completó lectura ID {lectura_id}"
    ))

    # 3. Actualizar contador de lecturas
    nivel = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == estudiante_id
    ).first()

    if nivel:
        nivel.lecturas_completadas += 1
        db.commit()

    # Logs automáticos:
    # 📊 Puntos registrados: +150 para Juan Pérez - Motivo: Completó lectura ID 10
    # 🎉 ¡Juan Pérez subió al nivel 3!
    # ✅ Puntos agregados exitosamente: Juan Pérez (2 → 3, +150 pts)
```

### Caso 2: Estudiante Completa Actividad

```python
def completar_actividad(db: Session, estudiante_id: int, actividad_id: int, calificacion: int):
    # Puntos basados en calificación
    if calificacion >= 90:
        puntos = 100
    elif calificacion >= 70:
        puntos = 75
    else:
        puntos = 50

    agregar_puntos_estudiante(db, HistorialPuntosCreate(
        estudiante_id=estudiante_id,
        puntos=puntos,
        motivo=f"Actividad {actividad_id} - Calificación: {calificacion}%"
    ))

    # Actualizar contador
    nivel = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == estudiante_id
    ).first()

    if nivel:
        nivel.actividades_completadas += 1
        db.commit()
```

### Caso 3: Racha Diaria

```python
from datetime import datetime, timedelta

def verificar_y_actualizar_racha(db: Session, estudiante_id: int):
    nivel = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == estudiante_id
    ).first()

    if not nivel:
        return

    # Verificar si practicó hoy
    hoy = datetime.now().date()

    # Si practicó, incrementar racha
    nivel.racha_actual += 1

    # Actualizar racha máxima si superó su récord
    if nivel.racha_actual > nivel.racha_maxima:
        nivel.racha_maxima = nivel.racha_actual

    # Bonus de puntos por racha
    if nivel.racha_actual >= 7:
        # Bonus semanal
        agregar_puntos_estudiante(db, HistorialPuntosCreate(
            estudiante_id=estudiante_id,
            puntos=200,
            motivo=f"¡Racha de {nivel.racha_actual} días!"
        ))

    db.commit()
```

### Caso 4: Penalización (Puntos Negativos)

```python
def aplicar_penalizacion(db: Session, estudiante_id: int, motivo: str):
    # Solo en casos extremos (ej: comportamiento inapropiado)
    agregar_puntos_estudiante(db, HistorialPuntosCreate(
        estudiante_id=estudiante_id,
        puntos=-50,  # Negativo
        motivo=f"Penalización: {motivo}"
    ))

    # Log:
    # ⚠️ Agregando puntos negativos (-50) a estudiante Juan Pérez - Motivo: Penalización: ...
```

---

## 🔄 Unificación de Lógica

### ❌ Problema Anterior

Existían **DOS implementaciones** de la misma lógica:

1. **Función PostgreSQL**: `agregar_puntos_estudiante(p_estudiante_id, p_puntos, p_motivo)`
   ```sql
   CREATE FUNCTION agregar_puntos_estudiante(...) RETURNS VOID AS $$
   BEGIN
     -- Insertar en historial_puntos
     -- Actualizar nivel_estudiante
     -- Lógica de subida de nivel
   END;
   $$ LANGUAGE plpgsql;
   ```

2. **Función Python**: `app.servicios.gamificacion.agregar_puntos_estudiante()`
   ```python
   def agregar_puntos_estudiante(db, puntos):
       # Insertar en historial_puntos
       # Actualizar nivel_estudiante
       # Lógica de subida de nivel
   ```

**Problemas**:
- ❌ Duplicación de lógica (violación de DRY)
- ❌ Difícil mantener consistencia
- ❌ Confusión sobre cuál usar
- ❌ Potencial de inconsistencias si se usan ambas

### ✅ Solución Implementada

**Decision: Centralizar en Python**

**Razones**:
1. ✅ **Ya está en uso**: El código actual usa la función Python
2. ✅ **Mejor mantenibilidad**: Código Python es más fácil de leer y modificar
3. ✅ **Mejor testeo**: Fácil crear unit tests
4. ✅ **Mejor logging**: Integración con sistema de logs de la app
5. ✅ **Mejor manejo de errores**: HTTPException con detalles
6. ✅ **Validaciones robustas**: Verificar que estudiante existe, crear nivel automáticamente
7. ✅ **Integración con FastAPI**: Dependency injection, sessions, etc.

**Acciones tomadas**:
1. ✅ **Mejorada** función Python con validaciones, logging y manejo de errores
2. ✅ **Creado** script de migración SQL para deprecar función PostgreSQL
3. ✅ **Documentado** la decisión en este README

### Migración

Ver archivo: `migrations/deprecar_funcion_agregar_puntos.sql`

**Opciones**:
1. **Eliminar** la función PostgreSQL (recomendado si no se usa)
2. **Renombrar** a `_deprecated_agregar_puntos_estudiante` (conservador)
3. **Reemplazar** con función que lance error si se intenta usar

---

## 📚 API Reference

### Endpoints de Puntos

#### Agregar Puntos
```http
POST /gamificacion/puntos
Content-Type: application/json

{
  "estudiante_id": 1,
  "puntos": 100,
  "motivo": "Completó lectura"
}

Response 200:
{
  "id": 42,
  "estudiante_id": 1,
  "puntos": 100,
  "motivo": "Completó lectura",
  "fecha": "2025-12-27T10:30:00"
}
```

#### Historial de Puntos
```http
GET /gamificacion/estudiante/{estudiante_id}/puntos?skip=0&limit=50

Response 200:
[
  {
    "id": 42,
    "estudiante_id": 1,
    "puntos": 100,
    "motivo": "Completó lectura",
    "fecha": "2025-12-27T10:30:00"
  },
  ...
]
```

#### Progreso del Estudiante
```http
GET /gamificacion/estudiante/{estudiante_id}/progreso

Response 200:
{
  "id": 1,
  "nombre": "Juan Pérez",
  "nivel_actual": 3,
  "xp_actual": 1500,
  "xp_para_siguiente_nivel": 3000,
  "racha_actual": 5
}
```

### Endpoints de Recompensas

#### Listar Recompensas Disponibles
```http
GET /gamificacion/recompensas?skip=0&limit=100&activo=true

Response 200:
[
  {
    "id": 1,
    "nombre": "Lector Principiante",
    "descripcion": "Completó su primera lectura",
    "tipo": "badge",
    "imagen_url": "/badges/lector_principiante.png",
    "puntos_requeridos": 100,
    "activo": true
  }
]
```

#### Asignar Recompensa
```http
POST /gamificacion/recompensas/estudiante
Content-Type: application/json

{
  "estudiante_id": 1,
  "recompensa_id": 5
}

Response 200:
{
  "id": 10,
  "estudiante_id": 1,
  "recompensa_id": 5,
  "fecha_obtencion": "2025-12-27T10:30:00"
}
```

### Endpoints de Misiones

#### Crear Misión Diaria
```http
POST /gamificacion/misiones
Content-Type: application/json

{
  "estudiante_id": 1,
  "descripcion": "Lee 3 textos hoy",
  "objetivo": 3,
  "puntos_recompensa": 50,
  "fecha": "2025-12-27"
}

Response 200:
{
  "id": 1,
  "estudiante_id": 1,
  "descripcion": "Lee 3 textos hoy",
  "objetivo": 3,
  "progreso": 0,
  "completada": false,
  "puntos_recompensa": 50,
  "fecha": "2025-12-27"
}
```

#### Actualizar Progreso de Misión
```http
PUT /gamificacion/misiones/{mision_id}/progreso?progreso=2

Response 200:
{
  "id": 1,
  "estudiante_id": 1,
  "descripcion": "Lee 3 textos hoy",
  "objetivo": 3,
  "progreso": 2,
  "completada": false,
  "puntos_recompensa": 50,
  "fecha": "2025-12-27"
}
```

---

## 🔍 Consultas SQL Útiles

### Ver progreso de todos los estudiantes
```sql
SELECT
    e.id,
    e.nombre,
    ne.nivel_actual,
    ne.puntos_totales,
    ne.puntos_nivel_actual,
    ne.puntos_para_siguiente_nivel,
    ne.racha_actual
FROM estudiante e
JOIN nivel_estudiante ne ON e.id = ne.estudiante_id
ORDER BY ne.nivel_actual DESC, ne.puntos_totales DESC
LIMIT 10;
```

### Top 10 estudiantes por puntos
```sql
SELECT
    e.nombre,
    ne.puntos_totales,
    ne.nivel_actual
FROM estudiante e
JOIN nivel_estudiante ne ON e.id = ne.estudiante_id
ORDER BY ne.puntos_totales DESC
LIMIT 10;
```

### Historial completo de un estudiante
```sql
SELECT
    fecha,
    puntos,
    motivo
FROM historial_puntos
WHERE estudiante_id = 1
ORDER BY fecha DESC
LIMIT 50;
```

### Puntos totales por motivo
```sql
SELECT
    motivo,
    COUNT(*) as veces,
    SUM(puntos) as total_puntos
FROM historial_puntos
WHERE estudiante_id = 1
GROUP BY motivo
ORDER BY total_puntos DESC;
```

---

## ✅ Mejores Prácticas

### 1. Siempre usar la función Python

```python
# ✅ CORRECTO
from app.servicios.gamificacion import agregar_puntos_estudiante
agregar_puntos_estudiante(db, puntos_data)

# ❌ INCORRECTO - NO usar función PostgreSQL
# db.execute("SELECT agregar_puntos_estudiante(...)")
```

### 2. Motivos descriptivos

```python
# ✅ CORRECTO - Motivo claro
motivo="Completó lectura 'El Principito' con 95% de precisión"

# ❌ INCORRECTO - Motivo vago
motivo="Lectura"
```

### 3. Manejar errores

```python
try:
    resultado = agregar_puntos_estudiante(db, puntos_data)
except HTTPException as e:
    # El estudiante no existe o hubo un error
    logger.error(f"Error al agregar puntos: {e.detail}")
    # Manejar el error apropiadamente
```

### 4. Verificar nivel antes de mostrar al usuario

```python
# Siempre consulta el nivel actualizado
nivel = db.query(NivelEstudiante).filter(
    NivelEstudiante.estudiante_id == estudiante_id
).first()

if not nivel:
    # El estudiante aún no tiene nivel, se creará al agregar puntos
    nivel_actual = 1
    xp_actual = 0
else:
    nivel_actual = nivel.nivel_actual
    xp_actual = nivel.puntos_nivel_actual
```

---

## 🐛 Troubleshooting

### Error: "Estudiante con ID X no encontrado"

```python
HTTPException(status_code=404, detail="Estudiante con ID 1 no encontrado")
```

**Solución**: Verifica que el estudiante existe antes de agregar puntos.

```python
estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
if not estudiante:
    raise HTTPException(status_code=404, detail="Estudiante no encontrado")
```

### Los puntos no se reflejan en el nivel

**Problema**: Agregaste puntos pero el nivel no cambió.

**Solución**: La función automáticamente maneja esto. Verifica los logs:
```
📈 Juan Pérez: 850/1000 XP (faltan 150 para nivel 2)
```

Si el estudiante tiene suficiente XP, verás:
```
🎉 ¡Juan Pérez subió al nivel 2!
```

### Función PostgreSQL sigue existiendo

**Solución**: Ejecutar la migración `migrations/deprecar_funcion_agregar_puntos.sql`

---

## 📖 Referencias

- **Código fuente**: `app/servicios/gamificacion.py`
- **Router**: `app/routers/gamificacion.py`
- **Modelos**: `app/modelos/nivel_estudiante.py`, `app/modelos/historial_puntos.py`
- **Esquemas**: `app/esquemas/gamificacion.py`
- **Migración SQL**: `migrations/deprecar_funcion_agregar_puntos.sql`

---

**Creado**: 2025-12-27
**Versión**: 2.0.0
**Sistema**: TutorIA - Backend - Gamificación Unificada
