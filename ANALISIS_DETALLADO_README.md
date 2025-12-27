# 📊 Sistema de Análisis Detallado de Evaluaciones

Documentación del sistema mejorado de análisis de lectura con almacenamiento granular de errores.

---

## 🎯 ¿Qué Cambió?

### ❌ **ANTES** (Pérdida de Datos):

```python
# Solo guardaba la evaluación general
evaluacion = EvaluacionLectura(...)
db.add(evaluacion)
db.commit()

# Los errores se retornaban pero NO se guardaban
return {
    "errores": analisis["errores_detectados"],  # ❌ Solo en memoria
    ...
}
```

**Problema**: Los errores detectados se perdían después de retornar. No había forma de:
- Consultar qué errores específicos cometió un estudiante
- Generar ejercicios personalizados posteriormente
- Analizar patrones de error a lo largo del tiempo
- Hacer seguimiento del progreso por palabra

### ✅ **AHORA** (Datos Persistentes):

```python
# 1. Guarda la evaluación general
evaluacion = EvaluacionLectura(...)
db.add(evaluacion)
db.commit()

# 2. Guarda CADA error con detalle
for error in errores_detectados:
    # Detalle de la palabra
    detalle = DetalleEvaluacion(
        evaluacion_id=evaluacion.id,
        palabra="palabra_incorrecta",
        posicion_en_texto=5,
        precision_pronunciacion=45.2,
        ...
    )
    db.add(detalle)

    # Error específico
    error_pron = ErrorPronunciacion(
        detalle_evaluacion_id=detalle.id,
        tipo_error="sustitucion",
        palabra_original="casa",
        palabra_detectada="caza",
        ...
    )
    db.add(error_pron)

db.commit()  # ✅ Todo persistido en BD
```

**Beneficio**: Ahora TODO se guarda en la base de datos de forma granular.

---

## 📋 Estructura de Datos

### Relaciones:

```
EvaluacionLectura (1)
    ↓
DetalleEvaluacion (N) - Uno por cada palabra con error
    ↓
ErrorPronunciacion (1) - El error específico de esa palabra
```

### Ejemplo Real:

**Texto esperado**: "El gato come pescado"
**Texto leído**: "El gato come pescao"

**Datos guardados**:

```sql
-- Evaluación General
INSERT INTO evaluacion_lectura (
    estudiante_id, contenido_id,
    puntuacion_pronunciacion, velocidad_lectura,
    precision_palabras, retroalimentacion_ia
) VALUES (
    1, 10,
    92.5, 85.2,
    92.5, '¡Muy bien! Cada vez lees mejor 👏'
);
-- Retorna: evaluacion_id = 42

-- Detalle por Palabra con Error
INSERT INTO detalle_evaluacion (
    evaluacion_id, palabra, posicion_en_texto,
    precision_pronunciacion, retroalimentacion_palabra
) VALUES (
    42, 'pescado', 3,
    75.0, 'Error de omision: esperado "pescado", leído "pescao"'
);
-- Retorna: detalle_id = 101

-- Error Específico
INSERT INTO error_pronunciacion (
    detalle_evaluacion_id, tipo_error,
    palabra_original, palabra_detectada,
    severidad, sugerencia_correccion
) VALUES (
    101, 'omision',
    'pescado', 'pescao',
    2, 'Practica pronunciar la palabra "pescado" correctamente...'
);
```

---

## 🔧 Funciones Nuevas

### 1. `_guardar_detalles_y_errores()` (en `ia_lectura_service.py`)

```python
def _guardar_detalles_y_errores(
    self,
    db: Session,
    evaluacion_id: int,
    tokens_leidos: List[str],
    errores_detectados: List[Dict]
):
    """
    Guarda DetalleEvaluacion y ErrorPronunciacion en BD.

    Por cada error:
    1. Crea un DetalleEvaluacion (palabra + precisión)
    2. Crea un ErrorPronunciacion (tipo + sugerencia)
    3. Los vincula mediante detalle_evaluacion_id
    """
```

**Características**:
- ✅ Guarda todos los errores detectados
- ✅ Calcula precisión por palabra usando similitud de Levenshtein
- ✅ Genera sugerencias de corrección automáticas
- ✅ Asocia cada error con su detalle mediante FK
- ✅ Log detallado de cuántos registros se guardaron

**Cuándo se llama**: Automáticamente después de cada `analizar_lectura()`

---

### 2. `crear_ejercicios_desde_bd()` (en `generador_ejercicios.py`)

```python
def crear_ejercicios_desde_bd(
    self,
    db: Session,
    evaluacion_id: int
) -> List[int]:
    """
    Crea ejercicios consultando errores desde la BD.

    No requiere recibir errores como parámetro,
    los consulta directamente de ErrorPronunciacion.
    """
```

**Ventajas sobre `crear_ejercicios_desde_errores`**:
- ✅ No requiere pasar errores como parámetro
- ✅ Usa datos ya persistidos en BD (source of truth)
- ✅ Permite crear ejercicios DESPUÉS de la evaluación
- ✅ Permite REGENERAR ejercicios si se necesita
- ✅ Consulta directa a la BD (más confiable)

**Uso**:

```python
from app.servicios.generador_ejercicios import GeneradorEjercicios

generador = GeneradorEjercicios()

# Crear ejercicios desde BD (en cualquier momento)
ejercicios_ids = generador.crear_ejercicios_desde_bd(
    db=db,
    evaluacion_id=42
)

print(f"Creados {len(ejercicios_ids)} ejercicios")
# Creados 3 ejercicios
```

---

## 📊 Datos Guardados por Error

Cada error detectado genera **2 registros**:

### 1. `detalle_evaluacion`

| Campo | Ejemplo | Descripción |
|-------|---------|-------------|
| `evaluacion_id` | 42 | FK a evaluacion_lectura |
| `palabra` | "pescado" | Palabra analizada |
| `posicion_en_texto` | 3 | Posición en el texto (0-indexed) |
| `precision_pronunciacion` | 75.0 | Similitud 0-100% |
| `retroalimentacion_palabra` | "Error de omision..." | Mensaje específico |
| `tipo_tokenizacion` | "word" | Tipo de token |

### 2. `error_pronunciacion`

| Campo | Ejemplo | Descripción |
|-------|---------|-------------|
| `detalle_evaluacion_id` | 101 | FK a detalle_evaluacion |
| `tipo_error` | "omision" | sustitucion/omision/insercion |
| `palabra_original` | "pescado" | Palabra esperada |
| `palabra_detectada` | "pescao" | Palabra pronunciada |
| `severidad` | 2 | 1-5 (bajo a alto) |
| `sugerencia_correccion` | "Practica..." | Ayuda para mejorar |

---

## 🎯 Casos de Uso

### Caso 1: Analizar Progreso del Estudiante

```python
# Obtener todos los errores de un estudiante
errores = db.query(ErrorPronunciacion).join(
    DetalleEvaluacion
).join(
    EvaluacionLectura
).filter(
    EvaluacionLectura.estudiante_id == 1
).all()

# Agrupar por tipo de error
from collections import Counter
tipos = Counter([e.tipo_error for e in errores])

print(f"Errores por tipo: {tipos}")
# Errores por tipo: {'omision': 15, 'sustitucion': 8, 'insercion': 3}
```

### Caso 2: Palabras Más Difíciles

```python
# Palabras con más errores
from sqlalchemy import func

palabras_dificiles = db.query(
    ErrorPronunciacion.palabra_original,
    func.count(ErrorPronunciacion.id).label('total')
).group_by(
    ErrorPronunciacion.palabra_original
).order_by(
    func.count(ErrorPronunciacion.id).desc()
).limit(10).all()

for palabra, total in palabras_dificiles:
    print(f"{palabra}: {total} errores")
# pescado: 5 errores
# trabajar: 4 errores
# ...
```

### Caso 3: Generar Ejercicios Personalizados

```python
# Después de una evaluación
evaluacion_id = 42

# Opción 1: Usar errores en memoria (inmediato)
generador.crear_ejercicios_desde_errores(
    db, estudiante_id, evaluacion_id, errores
)

# Opción 2: Usar errores de BD (en cualquier momento)
generador.crear_ejercicios_desde_bd(
    db, evaluacion_id
)

# Opción 3: Regenerar ejercicios si se necesita
generador.crear_ejercicios_desde_bd(
    db, evaluacion_id  # Mismo ID, nuevos ejercicios
)
```

### Caso 4: Dashboard de Docente

```python
# Estudiantes que cometen más errores de sustitución
estudiantes_con_sustitucion = db.query(
    EvaluacionLectura.estudiante_id,
    func.count(ErrorPronunciacion.id).label('total')
).join(
    DetalleEvaluacion
).join(
    ErrorPronunciacion
).filter(
    ErrorPronunciacion.tipo_error == 'sustitucion'
).group_by(
    EvaluacionLectura.estudiante_id
).order_by(
    func.count(ErrorPronunciacion.id).desc()
).all()
```

---

## 🔍 Consultas SQL Útiles

### Ver errores de una evaluación:

```sql
SELECT
    ep.tipo_error,
    ep.palabra_original,
    ep.palabra_detectada,
    de.precision_pronunciacion,
    de.retroalimentacion_palabra
FROM error_pronunciacion ep
JOIN detalle_evaluacion de ON ep.detalle_evaluacion_id = de.id
WHERE de.evaluacion_id = 42
ORDER BY de.posicion_en_texto;
```

### Estadísticas por estudiante:

```sql
SELECT
    e.estudiante_id,
    COUNT(DISTINCT e.id) as total_evaluaciones,
    COUNT(ep.id) as total_errores,
    AVG(e.puntuacion_pronunciacion) as promedio_precision
FROM evaluacion_lectura e
LEFT JOIN detalle_evaluacion de ON e.id = de.evaluacion_id
LEFT JOIN error_pronunciacion ep ON de.id = ep.detalle_evaluacion_id
WHERE e.estudiante_id = 1
GROUP BY e.estudiante_id;
```

### Palabras problemáticas globales:

```sql
SELECT
    palabra_original,
    COUNT(*) as veces_error,
    tipo_error,
    AVG(severidad) as severidad_promedio
FROM error_pronunciacion
WHERE palabra_original IS NOT NULL
GROUP BY palabra_original, tipo_error
HAVING COUNT(*) > 5
ORDER BY COUNT(*) DESC
LIMIT 20;
```

---

## ✅ Beneficios del Sistema Mejorado

### 1. **Trazabilidad Completa**
- ✅ Cada error queda registrado para siempre
- ✅ Permite análisis histórico del progreso
- ✅ Auditoría completa del aprendizaje

### 2. **Ejercicios Más Inteligentes**
- ✅ Basados en errores reales del estudiante
- ✅ Priorizan palabras con más dificultad
- ✅ Se pueden regenerar en cualquier momento

### 3. **Analytics Avanzados**
- ✅ Reportes de progreso detallados
- ✅ Identificación de patrones de error
- ✅ Comparación entre estudiantes
- ✅ Dashboard de docentes con insights

### 4. **Mejor Experiencia**
- ✅ Feedback más específico y útil
- ✅ Ejercicios verdaderamente personalizados
- ✅ Seguimiento del progreso palabra por palabra

---

## 🚀 Ejemplo de Flujo Completo

```python
# 1. Estudiante sube audio de lectura
resultado = servicio_ia.analizar_lectura(
    db=db,
    estudiante_id=1,
    contenido_id=10,
    audio_path="/uploads/audio/lectura_123.wav"
)

# Internamente:
# ✅ Transcribe audio con Whisper
# ✅ Compara con texto esperado
# ✅ Detecta errores (sustitucion, omision, etc.)
# ✅ Guarda EvaluacionLectura
# ✅ Guarda DetalleEvaluacion por cada error
# ✅ Guarda ErrorPronunciacion por cada error
# ✅ Retorna resultado con análisis

print(f"Evaluación ID: {resultado['evaluacion_id']}")
print(f"Precisión: {resultado['precision_global']}%")
print(f"Errores detectados: {len(resultado['errores'])}")

# 2. Generar ejercicios automáticamente desde BD
generador = GeneradorEjercicios()
ejercicios_ids = generador.crear_ejercicios_desde_bd(
    db=db,
    evaluacion_id=resultado['evaluacion_id']
)

print(f"Ejercicios creados: {len(ejercicios_ids)}")

# 3. Consultar progreso posterior
errores_estudiante = db.query(ErrorPronunciacion).join(
    DetalleEvaluacion
).join(
    EvaluacionLectura
).filter(
    EvaluacionLectura.estudiante_id == 1
).all()

print(f"Total de errores históricos: {len(errores_estudiante)}")
```

---

## 📝 Logging

El sistema registra automáticamente:

```
✅ Evaluación creada: ID=42, Precisión=92.5%
💾 Guardados 3 detalles de evaluación y 3 errores de pronunciación para evaluación 42
📚 Creando ejercicios desde 3 errores guardados en BD para evaluación 42
✅ 2 ejercicios creados desde BD para evaluación 42
```

---

## 🔐 Seguridad y Performance

### Transacciones Atómicas
```python
# Todo se guarda en una sola transacción
for error in errores:
    db.add(detalle)
    db.add(error_pron)

db.commit()  # Todo o nada
```

### Optimización de Queries
- Uso de `db.flush()` para obtener IDs sin commit
- JOIN eficientes en consultas
- Índices en FK para queries rápidas

---

**Creado**: 2025-12-27
**Versión**: 2.0.0
**Sistema**: TutorIA - Backend - Análisis IA Mejorado
