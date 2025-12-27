# 📚 ActividadLectura - Documentación

## Descripción

El modelo `ActividadLectura` representa actividades generadas automáticamente (por IA) o manualmente (por docentes) asociadas a contenidos de lectura. Este modelo permite crear preguntas de comprensión, vocabulario, y otros tipos de actividades educativas.

---

## 📋 Estructura del Modelo

### Tabla: `actividad_lectura`

| Campo | Tipo | Descripción | Por defecto |
|-------|------|-------------|-------------|
| `id` | BigInteger | ID único de la actividad | Auto-generado |
| `lectura_id` | BigInteger | FK a `contenido_lectura` | Requerido |
| `tipo` | String(50) | Tipo de actividad (ver tipos) | Requerido |
| `enunciado` | Text | Pregunta o enunciado de la actividad | Requerido |
| `opciones` | JSONB | Opciones de respuesta múltiple | NULL |
| `respuesta_correcta` | Text | Respuesta correcta | NULL |
| `explicacion` | Text | Explicación de la respuesta | NULL |
| `edad_min` | Integer | Edad mínima recomendada | 7 |
| `edad_max` | Integer | Edad máxima recomendada | 10 |
| `dificultad` | String(20) | Nivel de dificultad | 'media' |
| `origen` | String(20) | Origen de la actividad | 'ia' |
| `activo` | Boolean | Si está activa | true |
| `creado_en` | DateTime | Fecha de creación | CURRENT_TIMESTAMP |

---

## 🎯 Tipos de Actividad

Los tipos de actividad recomendados son:

- **`comprension`**: Preguntas de comprensión lectora
- **`vocabulario`**: Preguntas sobre vocabulario del texto
- **`inferencia`**: Preguntas que requieren inferencia
- **`secuencia`**: Ordenar eventos del texto
- **`personajes`**: Preguntas sobre personajes
- **`idea_principal`**: Identificar idea principal
- **`detalles`**: Recordar detalles específicos
- **`prediccion`**: Predecir qué sucederá
- **`causa_efecto`**: Relaciones causa-efecto

---

## 🔗 Relaciones

```
ContenidoLectura (1) ──────── (N) ActividadLectura
```

Una lectura puede tener múltiples actividades asociadas.

---

## 🚀 Endpoints Disponibles

### Base URL: `/api/actividades-lectura`

### 1. Crear Actividad de Lectura
```http
POST /api/actividades-lectura/
```

**Request Body:**
```json
{
  "lectura_id": 1,
  "tipo": "comprension",
  "enunciado": "¿Cuál es la idea principal del texto?",
  "opciones": {
    "a": "La naturaleza es hermosa",
    "b": "Los animales son importantes",
    "c": "Debemos cuidar el medio ambiente",
    "d": "El agua es esencial"
  },
  "respuesta_correcta": "c",
  "explicacion": "El texto se centra en la importancia de cuidar el medio ambiente",
  "edad_min": 7,
  "edad_max": 9,
  "dificultad": "media",
  "origen": "ia"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "lectura_id": 1,
  "tipo": "comprension",
  "enunciado": "¿Cuál es la idea principal del texto?",
  "opciones": {...},
  "respuesta_correcta": "c",
  "explicacion": "El texto se centra en la importancia de cuidar el medio ambiente",
  "edad_min": 7,
  "edad_max": 9,
  "dificultad": "media",
  "origen": "ia",
  "activo": true,
  "creado_en": "2025-12-27T10:00:00Z"
}
```

---

### 2. Listar Actividades
```http
GET /api/actividades-lectura/?skip=0&limit=100
```

**Query Parameters:**
- `skip` (int): Número de registros a saltar (paginación)
- `limit` (int): Máximo de registros a retornar (1-500)
- `lectura_id` (int, opcional): Filtrar por ID de lectura
- `tipo` (string, opcional): Filtrar por tipo de actividad
- `activo` (bool, opcional): Filtrar por estado activo/inactivo

**Ejemplo:**
```http
GET /api/actividades-lectura/?lectura_id=1&tipo=comprension&activo=true
```

---

### 3. Obtener Actividades por Edad
```http
GET /api/actividades-lectura/edad/{edad_estudiante}
```

Filtra automáticamente actividades apropiadas para la edad.

**Ejemplo:**
```http
GET /api/actividades-lectura/edad/8?lectura_id=1
```

Retorna solo actividades donde `edad_min <= 8 <= edad_max`.

---

### 4. Listar Actividades Generadas por IA
```http
GET /api/actividades-lectura/ia?lectura_id=1
```

Retorna solo actividades con `origen = 'ia'`.

---

### 5. Obtener Actividad Específica
```http
GET /api/actividades-lectura/{actividad_id}
```

**Ejemplo:**
```http
GET /api/actividades-lectura/1
```

---

### 6. Actualizar Actividad
```http
PUT /api/actividades-lectura/{actividad_id}
```

**Request Body** (todos los campos son opcionales):
```json
{
  "enunciado": "¿Cuál es el tema central del texto?",
  "dificultad": "dificil",
  "explicacion": "Explicación actualizada"
}
```

---

### 7. Desactivar Actividad (Soft Delete)
```http
DELETE /api/actividades-lectura/{actividad_id}
```

Marca la actividad como `activo = false` sin eliminarla físicamente.

**Response:**
```json
{
  "message": "Actividad de lectura desactivada exitosamente"
}
```

---

## 💻 Uso en Código Python

### Crear actividad desde un servicio

```python
from app.modelos import ActividadLectura
from app.esquemas.actividad_lectura import ActividadLecturaCreate
from app.servicios.actividad_lectura import crear_actividad_lectura

# Crear actividad
nueva_actividad = ActividadLecturaCreate(
    lectura_id=1,
    tipo="vocabulario",
    enunciado="¿Qué significa la palabra 'resiliencia'?",
    opciones={
        "a": "Fuerza física",
        "b": "Capacidad de recuperarse ante adversidades",
        "c": "Inteligencia",
        "d": "Habilidad matemática"
    },
    respuesta_correcta="b",
    explicacion="La resiliencia es la capacidad de adaptarse y recuperarse ante situaciones difíciles",
    edad_min=9,
    edad_max=12,
    dificultad="dificil"
)

actividad_guardada = crear_actividad_lectura(db, nueva_actividad)
```

### Consultar actividades

```python
from app.servicios.actividad_lectura import obtener_actividades_por_edad

# Obtener actividades apropiadas para un niño de 8 años
actividades = obtener_actividades_por_edad(db, edad_estudiante=8, lectura_id=1)

for actividad in actividades:
    print(f"Tipo: {actividad.tipo}")
    print(f"Enunciado: {actividad.enunciado}")
```

---

## 🤖 Integración con IA

Este modelo está diseñado para almacenar actividades generadas automáticamente por IA.

### Ejemplo de generación automática:

```python
# En el servicio de IA (app/servicios/ia_actividades.py)
from app.servicios.actividad_lectura import crear_actividad_lectura

def generar_actividades_automaticas(db, lectura_id: int, contenido_texto: str):
    """
    Genera actividades de comprensión usando IA basadas en el contenido
    """

    # Aquí iría la lógica de IA para generar preguntas
    # Por ejemplo, usando GPT para generar preguntas de comprensión

    actividad = ActividadLecturaCreate(
        lectura_id=lectura_id,
        tipo="comprension",
        enunciado=pregunta_generada_por_ia,
        opciones=opciones_generadas,
        respuesta_correcta=respuesta_correcta_ia,
        explicacion=explicacion_generada,
        origen="ia",  # Marca que fue generada por IA
        dificultad=nivel_detectado,
        edad_min=edad_min_detectada,
        edad_max=edad_max_detectada
    )

    return crear_actividad_lectura(db, actividad)
```

---

## 📊 Ejemplos de Opciones JSONB

### Opción Múltiple (Multiple Choice)
```json
{
  "a": "Primera opción",
  "b": "Segunda opción",
  "c": "Tercera opción",
  "d": "Cuarta opción"
}
```

### Verdadero/Falso
```json
{
  "verdadero": "El personaje principal es un niño",
  "falso": "El personaje principal es una niña"
}
```

### Emparejamiento
```json
{
  "pares": [
    {"termino": "Perro", "definicion": "Animal doméstico"},
    {"termino": "Gato", "definicion": "Felino casero"}
  ]
}
```

### Completar Espacios
```json
{
  "plantilla": "El _____ es un animal que vive en el agua",
  "opciones": ["pez", "ave", "perro", "gato"]
}
```

---

## 🔒 Seguridad y Permisos

Todos los endpoints requieren autenticación mediante JWT. Asegúrate de incluir el token en el header:

```http
Authorization: Bearer <tu_token_jwt>
```

---

## 📝 Notas Adicionales

1. **Soft Delete**: Las actividades nunca se eliminan físicamente, solo se marcan como `activo = false`
2. **Índice**: La tabla tiene un índice en `lectura_id` para búsquedas rápidas
3. **Cascade Delete**: Si se elimina un `ContenidoLectura`, todas sus actividades asociadas se eliminan automáticamente
4. **Origen**: El campo `origen` puede ser: `'ia'`, `'docente'`, o `'sistema'`
5. **Dificultad**: Los valores recomendados son: `'facil'`, `'media'`, `'dificil'`

---

## 🐛 Troubleshooting

### Error: "Contenido de lectura no encontrado"
```python
# Asegúrate de que el lectura_id existe
lectura = db.query(ContenidoLectura).filter(ContenidoLectura.id == lectura_id).first()
if not lectura:
    # Error: la lectura no existe
```

### Error: "actividad_lectura no se importa correctamente"
```python
# Asegúrate de importar desde app.modelos
from app.modelos import ActividadLectura
```

---

## ✅ Testing

Ejemplo de test unitario:

```python
def test_crear_actividad_lectura():
    actividad = ActividadLecturaCreate(
        lectura_id=1,
        tipo="comprension",
        enunciado="Pregunta de prueba",
        respuesta_correcta="a"
    )

    resultado = crear_actividad_lectura(db, actividad)

    assert resultado.id is not None
    assert resultado.tipo == "comprension"
    assert resultado.activo == True
    assert resultado.origen == "ia"
```

---

**Documentación creada:** 2025-12-27
**Versión:** 1.0.0
**Autor:** Sistema TutorIA
