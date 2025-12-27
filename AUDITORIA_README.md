# 🔍 Sistema de Auditoría TutorIA

Documentación completa del sistema de auditoría y trazabilidad de cambios.

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Problema Anterior](#problema-anterior)
3. [Solución Implementada](#solución-implementada)
4. [Arquitectura](#arquitectura)
5. [Uso en la Aplicación](#uso-en-la-aplicación)
6. [Triggers de PostgreSQL](#triggers-de-postgresql)
7. [Consultas y Reportes](#consultas-y-reportes)
8. [Mejores Prácticas](#mejores-prácticas)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El sistema de auditoría de TutorIA registra **automáticamente** todos los cambios en la base de datos:

- **Quién**: Usuario que hizo el cambio
- **Qué**: Acción realizada (INSERT, UPDATE, DELETE)
- **Cuándo**: Fecha y hora del evento
- **Dónde**: Tabla y registro afectado
- **Cómo**: Datos anteriores y nuevos (en formato JSON)
- **Desde dónde**: Dirección IP del usuario

---

## ❌ Problema Anterior

### Situación Original

Los triggers de PostgreSQL guardaban auditoría, **PERO** con un problema crítico:

```sql
-- Tabla auditoria
id              | accion  | tabla_afectada | usuario_id | ip_address
1               | UPDATE  | estudiante     | NULL       | NULL        ❌
2               | INSERT  | contenido      | NULL       | NULL        ❌
3               | DELETE  | docente        | NULL       | NULL        ❌
```

**Problemas**:
- ❌ `usuario_id` siempre era **NULL**
- ❌ No se sabía **quién** hizo cada cambio
- ❌ Imposible rastrear acciones de usuarios específicos
- ❌ No se capturaba la IP del cliente
- ❌ Auditoría incompleta e inútil para investigaciones

### ¿Por Qué Pasaba Esto?

Los triggers de PostgreSQL **NO tienen acceso al contexto de la aplicación**:
- No saben qué usuario está autenticado
- No tienen acceso al token JWT
- No conocen el objeto Request de FastAPI
- Solo ven la operación SQL en sí misma

---

## ✅ Solución Implementada

### Concepto: Variables de Sesión de PostgreSQL

PostgreSQL permite configurar variables de sesión que duran solo la transacción actual:

```sql
-- Python/SQLAlchemy configura variables
SET LOCAL app.current_user_id = 42;
SET LOCAL app.current_user_ip = '192.168.1.100';

-- Los triggers pueden leer esas variables
SELECT current_setting('app.current_user_id');  -- Retorna '42'
```

### Flujo Completo

```
1. Usuario hace request → POST /estudiantes
                          ↓
2. FastAPI autentica → Token JWT válido → Usuario ID = 42
                          ↓
3. Dependency configura contexto → SET LOCAL app.current_user_id = 42
                          ↓
4. Endpoint crea estudiante → INSERT INTO estudiante ...
                          ↓
5. Trigger se ejecuta → Lee current_setting('app.current_user_id')
                          ↓
6. Trigger guarda auditoría → INSERT INTO auditoria (usuario_id = 42, ...)
                          ↓
7. Resultado → ✅ Auditoría completa con usuario_id correcto
```

### Resultado

```sql
-- Tabla auditoria DESPUÉS de la migración
id  | accion  | tabla_afectada | usuario_id | ip_address     | fecha_evento
1   | UPDATE  | estudiante     | 42         | 192.168.1.100  | 2025-12-27 10:30:00  ✅
2   | INSERT  | contenido      | 15         | 10.0.2.45      | 2025-12-27 11:15:00  ✅
3   | DELETE  | docente        | 8          | 172.16.0.10    | 2025-12-27 12:00:00  ✅
```

**Ahora sí tenemos**:
- ✅ **Quién**: ID del usuario autenticado
- ✅ **Desde dónde**: IP del cliente
- ✅ **Trazabilidad completa**
- ✅ **Auditoría útil para investigaciones**

---

## 🏗️ Arquitectura

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIO / CLIENTE                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Request + JWT Token
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. obtener_usuario_actual()                         │   │
│  │     - Valida token JWT                               │   │
│  │     - Retorna Usuario (id=42)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  2. get_db_with_audit_context()                      │   │
│  │     - Configura: SET LOCAL app.current_user_id = 42  │   │
│  │     - Configura: SET LOCAL app.current_user_ip = ... │   │
│  │     - Retorna: Session                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  3. Endpoint Business Logic                          │   │
│  │     - db.add(estudiante)                             │   │
│  │     - db.commit()                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL: INSERT INTO estudiante ...
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      POSTGRESQL                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  4. Trigger: registrar_auditoria()                   │   │
│  │     - Lee: current_setting('app.current_user_id')    │   │
│  │     - Lee: current_setting('app.current_user_ip')    │   │
│  │     - Inserta en tabla auditoria                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tabla: auditoria                                    │   │
│  │  ├─ usuario_id: 42                  ✅               │   │
│  │  ├─ accion: INSERT                                   │   │
│  │  ├─ tabla_afectada: estudiante                       │   │
│  │  ├─ ip_address: 192.168.1.100       ✅               │   │
│  │  ├─ datos_nuevos: {...}                              │   │
│  │  └─ fecha_evento: NOW()                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `app/middlewares/audit_context.py` | Dependency que configura contexto de usuario |
| `migrations/mejorar_triggers_auditoria.sql` | Script SQL que actualiza triggers |
| `app/modelos/auditoria.py` | Modelo SQLAlchemy de la tabla auditoria |
| `app/esquemas/auditoria.py` | Schemas Pydantic para auditoría |
| `app/routers/auditoria.py` | API endpoints para consultar auditoría |

---

## 💻 Uso en la Aplicación

### Opción 1: Endpoints Autenticados (Recomendado)

Para endpoints que **requieren autenticación**, usa `get_db_with_audit_context`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.middlewares import get_db_with_audit_context
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Estudiante

router = APIRouter()

@router.post("/estudiantes")
def crear_estudiante(
    estudiante: EstudianteCreate,
    db: Session = Depends(get_db_with_audit_context),  # ✅ Usa esta dependency
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    El contexto de auditoría se configura automáticamente.
    Los triggers guardarán usuario_id = usuario_actual.id
    """
    nuevo = Estudiante(**estudiante.dict())
    db.add(nuevo)
    db.commit()  # Trigger se ejecuta aquí, guarda usuario_id correcto ✅
    return nuevo


@router.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(
    estudiante_id: int,
    datos: EstudianteUpdate,
    db: Session = Depends(get_db_with_audit_context),  # ✅
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    También funciona para UPDATE y DELETE
    """
    estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not estudiante:
        raise HTTPException(status_code=404)

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(estudiante, key, value)

    db.commit()  # Trigger guarda: accion=UPDATE, usuario_id=usuario_actual.id ✅
    return estudiante
```

### Opción 2: Endpoints Públicos (Sin Autenticación)

Para endpoints **públicos** como registro, login, etc., usa `get_db_with_audit_context_optional`:

```python
from app.middlewares import get_db_with_audit_context_optional

@router.post("/auth/register")
def registrar_usuario(
    datos: RegistroUsuario,
    db: Session = Depends(get_db_with_audit_context_optional)  # ✅ Opcional
):
    """
    No requiere autenticación, pero aún queremos auditar.
    Los triggers guardarán usuario_id = NULL (correcto, es operación pública)
    Pero SÍ capturarán la IP del cliente.
    """
    nuevo_usuario = Usuario(**datos.dict())
    db.add(nuevo_usuario)
    db.commit()  # Trigger guarda: usuario_id=NULL, ip_address="..." ✅
    return {"message": "Usuario creado"}
```

### Opción 3: Operaciones Manuales (Scripts, Batch)

Para scripts, migraciones, tareas asíncronas, etc.:

```python
from app.middlewares.audit_context import (
    configurar_contexto_auditoria_manual,
    limpiar_contexto_auditoria
)
from app.config import SessionLocal

# Script de migración
db = SessionLocal()

try:
    # Configurar contexto manualmente
    configurar_contexto_auditoria_manual(
        db=db,
        usuario_id=1,  # Usuario administrador que ejecuta el script
        ip_address="127.0.0.1"
    )

    # Hacer operaciones
    for estudiante in estudiantes_a_migrar:
        db.add(estudiante)

    db.commit()  # Todos los triggers guardarán usuario_id=1 ✅

finally:
    limpiar_contexto_auditoria(db)
    db.close()
```

---

## 🔧 Triggers de PostgreSQL

### Función: `registrar_auditoria()`

La función trigger mejorada hace lo siguiente:

```sql
CREATE OR REPLACE FUNCTION registrar_auditoria()
RETURNS TRIGGER AS $$
DECLARE
    v_usuario_id BIGINT;
    v_ip_address VARCHAR(50);
BEGIN
    -- 1. Leer contexto de la sesión
    BEGIN
        v_usuario_id := current_setting('app.current_user_id', TRUE)::BIGINT;
    EXCEPTION
        WHEN OTHERS THEN
            v_usuario_id := NULL;  -- Si no está configurado, usar NULL
    END;

    BEGIN
        v_ip_address := current_setting('app.current_user_ip', TRUE);
    EXCEPTION
        WHEN OTHERS THEN
            v_ip_address := NULL;
    END;

    -- 2. Insertar auditoría con contexto
    INSERT INTO auditoria (
        usuario_id,           -- ✅ Capturado del contexto
        accion,               -- INSERT, UPDATE, DELETE
        tabla_afectada,       -- Nombre de la tabla
        registro_id,          -- ID del registro
        datos_anteriores,     -- Estado anterior (JSON)
        datos_nuevos,         -- Estado nuevo (JSON)
        ip_address,          -- ✅ IP del cliente
        fecha_evento          -- Timestamp
    ) VALUES (
        v_usuario_id,
        TG_OP,
        TG_TABLE_NAME,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        v_ip_address,
        NOW()
    );

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;
```

### Tablas con Trigger de Auditoría

Estas tablas tienen el trigger `trigger_auditoria` activo:

- `usuario`
- `estudiante`
- `docente`
- `padre`
- `contenido_lectura`
- `evaluacion_lectura`
- `detalle_evaluacion`
- `actividad_lectura`
- `respuesta_actividad`
- `ejercicio_pronunciacion`
- `historial_puntos`
- `nivel_estudiante`
- `recompensa_estudiante`
- `mision_diaria`

### Verificar Triggers Instalados

```sql
SELECT
    trigger_schema,
    event_object_table AS tabla,
    trigger_name,
    event_manipulation AS evento
FROM information_schema.triggers
WHERE trigger_name = 'trigger_auditoria'
ORDER BY event_object_table;
```

---

## 📊 Consultas y Reportes

### Ver Auditoría Reciente

```sql
SELECT
    a.id,
    a.fecha_evento,
    u.email AS usuario,
    a.accion,
    a.tabla_afectada,
    a.registro_id,
    a.ip_address
FROM auditoria a
LEFT JOIN usuario u ON a.usuario_id = u.id
ORDER BY a.fecha_evento DESC
LIMIT 50;
```

### Actividad de un Usuario Específico

```sql
SELECT
    a.fecha_evento,
    a.accion,
    a.tabla_afectada,
    a.registro_id,
    a.datos_anteriores,
    a.datos_nuevos
FROM auditoria a
WHERE a.usuario_id = 42
ORDER BY a.fecha_evento DESC;
```

### Cambios en un Registro Específico

```sql
-- Ver historial completo de un estudiante
SELECT
    a.fecha_evento,
    u.email AS modificado_por,
    a.accion,
    a.datos_anteriores,
    a.datos_nuevos
FROM auditoria a
LEFT JOIN usuario u ON a.usuario_id = u.id
WHERE a.tabla_afectada = 'estudiante'
  AND a.registro_id = 10
ORDER BY a.fecha_evento;
```

### Top Usuarios Más Activos

```sql
SELECT
    u.email,
    u.nombre,
    COUNT(*) as total_operaciones,
    COUNT(CASE WHEN a.accion = 'INSERT' THEN 1 END) as inserts,
    COUNT(CASE WHEN a.accion = 'UPDATE' THEN 1 END) as updates,
    COUNT(CASE WHEN a.accion = 'DELETE' THEN 1 END) as deletes,
    MAX(a.fecha_evento) as ultima_actividad
FROM auditoria a
JOIN usuario u ON a.usuario_id = u.id
GROUP BY u.id, u.email, u.nombre
ORDER BY total_operaciones DESC
LIMIT 10;
```

### Operaciones por Tabla

```sql
SELECT
    tabla_afectada,
    accion,
    COUNT(*) as total
FROM auditoria
WHERE fecha_evento >= NOW() - INTERVAL '7 days'
GROUP BY tabla_afectada, accion
ORDER BY total DESC;
```

### Auditoría Sin Usuario (Operaciones Públicas o Antiguas)

```sql
SELECT
    tabla_afectada,
    accion,
    COUNT(*) as total,
    MAX(fecha_evento) as ultima_vez
FROM auditoria
WHERE usuario_id IS NULL
GROUP BY tabla_afectada, accion
ORDER BY total DESC;
```

### Actividad por IP

```sql
SELECT
    ip_address,
    COUNT(*) as operaciones,
    COUNT(DISTINCT usuario_id) as usuarios_diferentes,
    MIN(fecha_evento) as primera_actividad,
    MAX(fecha_evento) as ultima_actividad
FROM auditoria
WHERE ip_address IS NOT NULL
GROUP BY ip_address
ORDER BY operaciones DESC;
```

---

## 📚 Mejores Prácticas

### 1. Usar la Dependency Correcta

```python
# ✅ CORRECTO - Para endpoints autenticados
@router.post("/recursos")
def crear(
    db: Session = Depends(get_db_with_audit_context),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    ...

# ✅ CORRECTO - Para endpoints públicos
@router.post("/auth/login")
def login(
    db: Session = Depends(get_db_with_audit_context_optional)
):
    ...

# ❌ INCORRECTO - No captura contexto de usuario
@router.post("/recursos")
def crear(
    db: Session = Depends(get_db),  # ❌ Auditoría incompleta
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    ...
```

### 2. Migración Gradual

No es necesario cambiar todos los endpoints de una vez:

```python
# Prioridad ALTA - Cambiar primero
- Operaciones críticas: DELETE de estudiantes, docentes
- Cambios de configuración: actualizar roles, permisos
- Operaciones administrativas: crear/editar contenido

# Prioridad MEDIA - Cambiar después
- CRUD normal: crear lecturas, actividades
- Operaciones de estudiantes: completar actividades

# Prioridad BAJA - Puede esperar
- Consultas read-only (GET)
- Endpoints de estadísticas
```

### 3. Revisar Auditoría Regularmente

```python
# Crear endpoint para administradores
@router.get("/admin/auditoria/resumen")
def resumen_auditoria(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_rol_admin)
):
    """
    Dashboard de auditoría para administradores
    """
    return {
        "operaciones_hoy": db.query(Auditoria).filter(
            Auditoria.fecha_evento >= date.today()
        ).count(),

        "usuarios_activos_hoy": db.query(Auditoria.usuario_id).filter(
            Auditoria.fecha_evento >= date.today(),
            Auditoria.usuario_id.isnot(None)
        ).distinct().count(),

        "operaciones_sin_usuario": db.query(Auditoria).filter(
            Auditoria.usuario_id.is_(None)
        ).count()
    }
```

### 4. Limpieza de Auditoría Antigua

```sql
-- Archivar auditoría antigua (> 1 año) en tabla separada
INSERT INTO auditoria_historica
SELECT * FROM auditoria
WHERE fecha_evento < NOW() - INTERVAL '1 year';

-- Eliminar de tabla principal
DELETE FROM auditoria
WHERE fecha_evento < NOW() - INTERVAL '1 year';

-- O configurar particionamiento por fecha
```

---

## 🐛 Troubleshooting

### Problema: `usuario_id` sigue siendo NULL

**Síntomas**: Después de la migración, la auditoría sigue sin capturar el usuario_id.

**Diagnóstico**:

1. Verificar que el trigger está actualizado:
```sql
SELECT prosrc FROM pg_proc WHERE proname = 'registrar_auditoria';
-- Debe incluir current_setting('app.current_user_id')
```

2. Verificar que se está usando la dependency correcta:
```python
# ❌ MAL
db: Session = Depends(get_db)

# ✅ BIEN
db: Session = Depends(get_db_with_audit_context)
```

3. Verificar logs de la aplicación:
```
Debe aparecer: 🔐 Contexto de auditoría configurado: usuario_id=42
```

**Solución**: Actualizar el endpoint para usar `get_db_with_audit_context`.

---

### Problema: Error "unrecognized configuration parameter"

**Error completo**:
```
ERROR: unrecognized configuration parameter "app.current_user_id"
```

**Causa**: PostgreSQL versión < 9.2 no soporta variables de sesión custom.

**Solución**: Actualizar PostgreSQL a versión >= 9.2 (recomendado >= 12).

---

### Problema: IP siempre es NULL o 127.0.0.1

**Síntomas**: `ip_address` en auditoría es NULL o siempre muestra localhost.

**Causa**: La aplicación está detrás de un proxy/load balancer.

**Solución**: Verificar que el proxy pasa los headers correctos:

```python
# En get_db_with_audit_context, verifica headers:
if 'x-forwarded-for' in request.headers:
    ip_address = request.headers['x-forwarded-for'].split(',')[0]
elif 'x-real-ip' in request.headers:
    ip_address = request.headers['x-real-ip']
else:
    ip_address = request.client.host
```

---

### Problema: Datos JSON muy grandes en auditoría

**Síntomas**: Tabla `auditoria` crece rápidamente, queries lentas.

**Causa**: Los campos `datos_anteriores` y `datos_nuevos` guardan JSONB completo.

**Soluciones**:

1. **Filtrar campos sensibles** en el trigger:
```sql
-- Modificar trigger para excluir campos grandes
v_datos_nuevos := to_jsonb(NEW) - 'imagen_perfil' - 'archivo_adjunto';
```

2. **Particionar tabla** por fecha:
```sql
CREATE TABLE auditoria_2025_01 PARTITION OF auditoria
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

3. **Archivar datos antiguos** periódicamente.

---

## 🔒 Seguridad

### ¿Se puede falsificar el usuario_id?

**NO**. El usuario_id viene del token JWT validado por FastAPI:

1. Cliente envía JWT token
2. FastAPI valida firma y expiración
3. Si es válido, extrae `usuario_id` del payload
4. La aplicación (backend) configura `SET LOCAL app.current_user_id`
5. El cliente NO puede modificar variables de sesión de PostgreSQL

### ¿Qué pasa si alguien se conecta directo a PostgreSQL?

Si alguien se conecta directamente a la BD (no a través de la API):
- Las variables de sesión NO estarán configuradas
- Los triggers guardarán `usuario_id = NULL`
- Es correcto: no sabemos quién fue (operación fuera de la app)

**Recomendación**: Usar permisos de PostgreSQL para restringir conexiones directas.

---

## 📖 Referencias

- **Código fuente**: `app/middlewares/audit_context.py`
- **Migración SQL**: `migrations/mejorar_triggers_auditoria.sql`
- **Modelo**: `app/modelos/auditoria.py`
- **Router**: `app/routers/auditoria.py`
- **PostgreSQL Docs**: [SET configuration parameter](https://www.postgresql.org/docs/current/sql-set.html)

---

**Creado**: 2025-12-27
**Versión**: 2.0.0
**Sistema**: TutorIA - Backend - Auditoría con Contexto de Usuario
