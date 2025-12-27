# 🤖 Generador Automático de Actividades con IA

Sistema inteligente que analiza contenidos de lectura y genera automáticamente preguntas y actividades educativas adaptadas al nivel del estudiante.

---

## 📋 ¿Qué hace?

El generador de actividades con IA toma un texto de lectura y automáticamente crea:

✅ **Preguntas de comprensión lectora**
✅ **Preguntas de vocabulario** (palabras clave del texto)
✅ **Preguntas sobre la idea principal**
✅ **Preguntas de inferencia** (deducciones)
✅ **Preguntas sobre detalles específicos** (nombres, lugares, eventos)

---

## 🚀 Cómo Usar

### Endpoint Principal

```http
POST /api/actividades-lectura/generar/{lectura_id}
```

### Ejemplo Básico

```bash
curl -X POST http://localhost:8000/api/actividades-lectura/generar/1 \
  -H "Authorization: Bearer <tu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "num_actividades": 5
  }'
```

### Ejemplo Avanzado (Tipos Específicos)

```bash
curl -X POST http://localhost:8000/api/actividades-lectura/generar/1 \
  -H "Authorization: Bearer <tu_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "num_actividades": 3,
    "tipos": ["comprension", "vocabulario", "idea_principal"]
  }'
```

### Ejemplo desde Python

```python
import requests

url = "http://localhost:8000/api/actividades-lectura/generar/1"
headers = {"Authorization": f"Bearer {token}"}

# Generar 5 actividades de todos los tipos
response = requests.post(
    url,
    headers=headers,
    json={"num_actividades": 5}
)

resultado = response.json()
print(f"Generadas {resultado['total_generadas']} actividades")
for actividad in resultado['actividades']:
    print(f"- {actividad['tipo']}: {actividad['enunciado']}")
```

---

## 📊 Tipos de Actividades

### 1. **Comprensión** (`comprension`)
Evalúa el entendimiento general del texto.

**Ejemplo**:
```json
{
  "tipo": "comprension",
  "enunciado": "¿Qué sucede en esta historia?",
  "opciones": {
    "a": "Se describe un evento importante",
    "b": "Se presenta un conflicto",
    "c": "Se resuelve una situación",
    "d": "Se introduce un personaje"
  },
  "respuesta_correcta": "a"
}
```

### 2. **Vocabulario** (`vocabulario`)
Pregunta sobre el significado de palabras clave del texto.

**Ejemplo**:
```json
{
  "tipo": "vocabulario",
  "enunciado": "¿Qué significa la palabra 'resiliencia'?",
  "opciones": {
    "a": "Capacidad de recuperarse ante adversidades",
    "b": "Fuerza física",
    "c": "Inteligencia",
    "d": "Habilidad matemática"
  },
  "respuesta_correcta": "a"
}
```

### 3. **Idea Principal** (`idea_principal`)
Identifica el tema o mensaje central del texto.

**Ejemplo**:
```json
{
  "tipo": "idea_principal",
  "enunciado": "¿Cuál es la idea principal del texto?",
  "opciones": {
    "a": "El texto habla sobre un tema importante",
    "b": "El texto no tiene un tema claro",
    "c": "El texto habla sobre varios temas sin relación",
    "d": "El texto es solo entretenimiento"
  },
  "respuesta_correcta": "a"
}
```

### 4. **Inferencia** (`inferencia`)
Requiere deducir información no explícita.

**Ejemplo**:
```json
{
  "tipo": "inferencia",
  "enunciado": "Según el texto, ¿qué puedes inferir?",
  "opciones": {
    "a": "El autor tiene un mensaje que quiere compartir",
    "b": "El texto no tiene ningún propósito",
    "c": "Solo es importante lo que dice literalmente",
    "d": "No se puede inferir nada"
  },
  "respuesta_correcta": "a"
}
```

### 5. **Detalles** (`detalles`)
Pregunta sobre información específica mencionada en el texto.

**Ejemplo**:
```json
{
  "tipo": "detalles",
  "enunciado": "¿Qué se menciona sobre 'Pedro' en el texto?",
  "opciones": {
    "a": "Pedro es mencionado en el texto",
    "b": "Pedro no aparece en el texto",
    "c": "Pedro es el autor",
    "d": "No hay suficiente información"
  },
  "respuesta_correcta": "a"
}
```

---

## 🧠 Cómo Funciona el Análisis

### 1. **Análisis del Texto**

El sistema analiza el contenido y extrae:

- **Oraciones**: Divide el texto en oraciones individuales
- **Palabras clave**: Identifica las palabras más importantes (frecuencia)
- **Nombres propios**: Detecta nombres de personas, lugares, etc.
- **Estructura**: Primera oración, última oración, longitud total

### 2. **Generación Inteligente**

Según el análisis, genera preguntas que:

- **Se adaptan a la edad** del estudiante (edad_min, edad_max)
- **Respetan el nivel de dificultad** del contenido
- **Usan vocabulario del texto** (palabras reales del contenido)
- **Son contextualmente relevantes** (basadas en el contenido real)

### 3. **Guardado Automático**

Todas las actividades generadas:

- ✅ Se guardan en la tabla `actividad_lectura`
- ✅ Quedan asociadas a la lectura (`lectura_id`)
- ✅ Se marcan con `origen = 'ia'`
- ✅ Se pueden editar manualmente después

---

## 📝 Request y Response

### Request Body

```typescript
{
  num_actividades: number;  // Número de actividades a generar (default: 5)
  tipos?: string[];         // Tipos específicos (opcional)
}
```

### Response

```typescript
{
  lectura_id: number;                    // ID de la lectura
  lectura_titulo: string;                // Título de la lectura
  total_generadas: number;               // Total de actividades creadas
  actividades: ActividadLecturaResponse[] // Lista de actividades
}
```

### Ejemplo de Response Completo

```json
{
  "lectura_id": 1,
  "lectura_titulo": "El Principito",
  "total_generadas": 3,
  "actividades": [
    {
      "id": 101,
      "lectura_id": 1,
      "tipo": "comprension",
      "enunciado": "¿Qué sucede en esta historia?",
      "opciones": {
        "a": "Se describe un evento importante",
        "b": "Se presenta un conflicto",
        "c": "Se resuelve una situación",
        "d": "Se introduce un personaje"
      },
      "respuesta_correcta": "a",
      "explicacion": "La lectura describe eventos importantes...",
      "edad_min": 7,
      "edad_max": 9,
      "dificultad": "media",
      "origen": "ia",
      "activo": true,
      "creado_en": "2025-12-27T12:00:00Z"
    },
    {
      "id": 102,
      "lectura_id": 1,
      "tipo": "vocabulario",
      "enunciado": "¿Qué significa la palabra 'principito'?",
      "opciones": {...},
      "respuesta_correcta": "b",
      ...
    },
    {
      "id": 103,
      "lectura_id": 1,
      "tipo": "idea_principal",
      "enunciado": "¿Cuál es la idea principal del texto?",
      "opciones": {...},
      "respuesta_correcta": "a",
      ...
    }
  ]
}
```

---

## 💡 Casos de Uso

### 1. Docente Crea una Nueva Lectura

```python
# 1. El docente crea un contenido de lectura
contenido = crear_contenido_lectura(
    titulo="Los Animales del Bosque",
    contenido="Había una vez en el bosque...",
    edad_recomendada=8,
    nivel_dificultad=2
)

# 2. Automáticamente genera actividades para ese contenido
response = requests.post(
    f"/api/actividades-lectura/generar/{contenido.id}",
    json={"num_actividades": 5}
)

# ✅ Ya tiene 5 actividades listas para sus estudiantes
```

### 2. Generar Solo Tipos Específicos

```python
# Generar solo preguntas de comprensión y vocabulario
response = requests.post(
    f"/api/actividades-lectura/generar/1",
    json={
        "num_actividades": 4,
        "tipos": ["comprension", "vocabulario"]
    }
)
```

### 3. Re-generar Actividades

```python
# Si no gustan las actividades, se pueden generar nuevas
# (las anteriores quedan guardadas)
response = requests.post(
    f"/api/actividades-lectura/generar/1",
    json={"num_actividades": 3}
)
```

---

## 🎯 Ventajas

### ✅ **Ahorro de Tiempo**
Los docentes no tienen que crear manualmente preguntas para cada lectura.

### ✅ **Consistencia**
Todas las lecturas tienen actividades de calidad similar.

### ✅ **Adaptabilidad**
Las actividades se adaptan automáticamente al nivel y edad de la lectura.

### ✅ **Escalabilidad**
Se pueden generar cientos de actividades en segundos.

### ✅ **Mejora Continua**
Las actividades generadas se pueden editar y mejorar manualmente después.

---

## 🔧 Personalización Posterior

Las actividades generadas por IA **se pueden editar**:

```http
PUT /api/actividades-lectura/{actividad_id}
```

```json
{
  "enunciado": "Pregunta mejorada por el docente",
  "explicacion": "Explicación más detallada",
  "dificultad": "dificil"
}
```

---

## 📊 Análisis de Texto

### Palabras Clave

El sistema identifica palabras importantes:

1. Filtra palabras comunes ('el', 'la', 'un', 'de', etc.)
2. Cuenta frecuencia de palabras restantes
3. Prioriza palabras más largas (>4 caracteres)
4. Retorna las 10 palabras más importantes

### Nombres Propios

Detecta automáticamente:
- Nombres de personas
- Nombres de lugares
- Otros nombres relevantes

Usa estas detecciones para generar preguntas sobre **detalles específicos**.

---

## ⚙️ Configuración

### Edad y Dificultad

Las actividades generadas heredan:

- `edad_min` = edad_recomendada - 1 (mínimo 5)
- `edad_max` = edad_recomendada + 1 (máximo 12)
- `dificultad` = mapeo del nivel_dificultad:
  - Nivel 1-2 → "facil"
  - Nivel 3 → "media"
  - Nivel 4-5 → "dificil"

---

## 🐛 Manejo de Errores

### Error: Lectura No Encontrada

```json
{
  "detail": "Contenido de lectura con ID 999 no encontrado"
}
```
**Status**: 404

### Error: Sin Autenticación

```json
{
  "detail": "No se pudieron validar las credenciales"
}
```
**Status**: 401

### Error en Generación

```json
{
  "detail": "Error al generar actividades: <detalle>"
}
```
**Status**: 500

---

## 📈 Mejoras Futuras

Este generador es una **base inicial**. Puede mejorarse con:

1. **Integración con GPT** (OpenAI API) para preguntas más sofisticadas
2. **Análisis semántico** más profundo del texto
3. **Sinónimos reales** para opciones de vocabulario
4. **Detección de conceptos** clave automática
5. **Preguntas de ordenar eventos** basadas en la cronología del texto
6. **Preguntas de causa-efecto** automáticas

---

## 🔐 Seguridad

- ✅ Requiere autenticación JWT
- ✅ Solo docentes y admins pueden generar actividades
- ✅ Valida que el contenido de lectura exista
- ✅ Maneja errores de forma segura

---

## 📚 Documentación Relacionada

- [ActividadLectura Modelo](ACTIVIDAD_LECTURA_README.md)
- [API REST Endpoints](ACTIVIDAD_LECTURA_README.md#-endpoints-disponibles)

---

**Creado**: 2025-12-27
**Versión**: 1.0.0
**Sistema**: TutorIA - Backend
