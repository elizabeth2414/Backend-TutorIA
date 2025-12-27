# 🔐 Sistema de Roles y Autorización TutorIA

Documentación completa del sistema de roles, permisos y validación de acceso.

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Roles Disponibles](#roles-disponibles)
3. [Arquitectura](#arquitectura)
4. [Dependencies de Validación](#dependencies-de-validación)
5. [Uso en Endpoints](#uso-en-endpoints)
6. [Casos de Uso](#casos-de-uso)
7. [Mejores Prácticas](#mejores-prácticas)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El sistema de roles de TutorIA permite controlar el acceso a endpoints y funcionalidades basándose en el rol del usuario autenticado.

### Características

- ✅ **Validación automática**: Dependencies que verifican roles antes de ejecutar endpoints
- ✅ **Múltiples roles por usuario**: Un usuario puede tener varios roles activos
- ✅ **Roles temporales**: Soporta expiración de roles
- ✅ **Logging detallado**: Registra intentos de acceso denegado
- ✅ **Mensajes claros**: Errores HTTP 403 con detalles de rol requerido
- ✅ **Flexible**: Dependencies para validar uno, múltiples o todos los roles

---

## 👥 Roles Disponibles

### Roles del Sistema

El sistema maneja 4 roles principales:

| Rol | Descripción | Permisos Típicos |
|-----|-------------|------------------|
| `admin` | Administrador del sistema | Acceso completo, gestión de usuarios, configuración |
| `docente` | Profesor/Instructor | Crear contenido, ver estudiantes, calificar |
| `estudiante` | Alumno | Realizar lecturas, actividades, ver su progreso |
| `padre` | Padre/Tutor | Ver progreso de hijos, recibir notificaciones |

### Modelo de Datos

```python
# Tabla: usuario_rol
class UsuarioRol:
    id: int
    usuario_id: int          # FK → usuario.id
    rol: str                 # 'admin', 'docente', 'estudiante', 'padre'
    activo: bool             # Si el rol está activo
    fecha_asignacion: datetime
    fecha_expiracion: datetime | None  # Opcional: cuando expira el rol
```

**Constraint de base de datos**:
```sql
CHECK (rol IN ('estudiante', 'docente', 'padre', 'admin'))
```

---

## 🏗️ Arquitectura

### Flujo de Validación

```
1. Cliente hace request → GET /admin/dashboard + JWT Token
                          ↓
2. FastAPI → obtener_usuario_actual()
            Valida token JWT
            Retorna: Usuario (id=42, email="admin@tutoria.com")
                          ↓
3. Dependency → requiere_admin()
               Consulta: SELECT * FROM usuario_rol
                         WHERE usuario_id = 42
                         AND rol = 'admin'
                         AND activo = true
                          ↓
4. Verificación:
   - Si tiene rol admin → ✅ Continúa al endpoint
   - Si NO tiene rol    → ❌ HTTPException 403
                          ↓
5. Endpoint ejecuta lógica de negocio
                          ↓
6. Response al cliente
```

### Componentes

**Funciones auxiliares** (`app/servicios/seguridad.py`):
- `verificar_rol(db, usuario_id, rol)` → bool
- `obtener_roles_usuario(db, usuario_id)` → List[str]

**Dependencies básicas**:
- `requiere_admin()` → Valida rol admin
- `requiere_docente()` → Valida rol docente
- `requiere_estudiante()` → Valida rol estudiante
- `requiere_padre()` → Valida rol padre

**Dependencies avanzadas**:
- `requiere_cualquier_rol(*roles)` → Valida AL MENOS UNO de los roles
- `requiere_todos_los_roles(*roles)` → Valida TODOS los roles

---

## 🛡️ Dependencies de Validación

### 1. Validación de Rol Único

#### `requiere_admin()`

Valida que el usuario tenga rol `admin`.

```python
from fastapi import APIRouter, Depends
from app.servicios.seguridad import requiere_admin
from app.modelos import Usuario

router = APIRouter()

@router.post("/admin/usuarios")
def crear_usuario(
    datos: UsuarioCreate,
    admin: Usuario = Depends(requiere_admin)  # ✅ Solo admins
):
    """Solo administradores pueden crear usuarios"""
    nuevo_usuario = crear_nuevo_usuario(datos)
    return nuevo_usuario
```

**Comportamiento**:
- ✅ Si el usuario tiene rol `admin` activo → Permite acceso
- ❌ Si NO tiene rol admin → HTTPException 403
- 📝 Log: `⚠️ Acceso denegado: user@example.com intentó acceder a endpoint admin sin permisos`

---

#### `requiere_docente()`

Valida que el usuario tenga rol `docente`.

```python
from app.servicios.seguridad import requiere_docente

@router.get("/docentes/mis-cursos")
def obtener_mis_cursos(
    docente: Usuario = Depends(requiere_docente)  # ✅ Solo docentes
):
    """Solo docentes pueden ver sus cursos"""
    cursos = obtener_cursos_docente(docente.id)
    return cursos
```

---

#### `requiere_estudiante()`

Valida que el usuario tenga rol `estudiante`.

```python
from app.servicios.seguridad import requiere_estudiante

@router.get("/estudiantes/mi-progreso")
def obtener_mi_progreso(
    estudiante: Usuario = Depends(requiere_estudiante)  # ✅ Solo estudiantes
):
    """Solo estudiantes pueden ver su propio progreso"""
    progreso = calcular_progreso_estudiante(estudiante.id)
    return progreso
```

---

#### `requiere_padre()`

Valida que el usuario tenga rol `padre`.

```python
from app.servicios.seguridad import requiere_padre

@router.get("/padres/mis-hijos")
def obtener_mis_hijos(
    padre: Usuario = Depends(requiere_padre)  # ✅ Solo padres/tutores
):
    """Solo padres pueden ver información de sus hijos"""
    hijos = obtener_hijos_padre(padre.id)
    return hijos
```

---

### 2. Validación de Múltiples Roles

#### `requiere_cualquier_rol(*roles)`

Factory function que valida **AL MENOS UNO** de los roles especificados.

**Uso 1: Admin O Docente**

```python
from app.servicios.seguridad import requiere_cualquier_rol

@router.post("/contenido")
def crear_contenido(
    contenido: ContenidoCreate,
    usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente"))
):
    """
    Administradores Y docentes pueden crear contenido.
    El usuario necesita tener admin O docente (al menos uno).
    """
    nuevo_contenido = crear_nuevo_contenido(contenido, usuario.id)
    return nuevo_contenido
```

**Comportamiento**:
- Usuario con rol `admin` → ✅ Acceso permitido
- Usuario con rol `docente` → ✅ Acceso permitido
- Usuario con ambos roles → ✅ Acceso permitido
- Usuario con rol `estudiante` → ❌ HTTPException 403

---

**Uso 2: Ver Progreso de Estudiante (Admin, Docente o Padre)**

```python
@router.get("/estudiantes/{estudiante_id}/progreso")
def ver_progreso_estudiante(
    estudiante_id: int,
    usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente", "padre"))
):
    """
    Múltiples roles pueden ver el progreso:
    - Admin: puede ver cualquier estudiante
    - Docente: puede ver sus estudiantes
    - Padre: puede ver a sus hijos
    """

    # Lógica adicional para verificar relación
    if "docente" in obtener_roles_usuario(db, usuario.id):
        # Verificar que el estudiante está en un curso del docente
        ...
    elif "padre" in obtener_roles_usuario(db, usuario.id):
        # Verificar que el estudiante es hijo del padre
        ...

    progreso = obtener_progreso(estudiante_id)
    return progreso
```

---

#### `requiere_todos_los_roles(*roles)`

Factory function que valida que el usuario tenga **TODOS** los roles especificados.

```python
from app.servicios.seguridad import requiere_todos_los_roles

@router.post("/admin/cursos/especiales")
def crear_curso_especial(
    curso: CursoCreate,
    usuario: Usuario = Depends(requiere_todos_los_roles("admin", "docente"))
):
    """
    Solo usuarios que tienen AMBOS roles pueden crear cursos especiales.
    El usuario debe ser admin Y docente simultáneamente.
    """
    nuevo_curso = crear_curso_especial(curso)
    return nuevo_curso
```

**Comportamiento**:
- Usuario con roles `['admin', 'docente']` → ✅ Acceso permitido
- Usuario con solo `['admin']` → ❌ HTTPException 403 (falta 'docente')
- Usuario con solo `['docente']` → ❌ HTTPException 403 (falta 'admin')

---

## 📝 Uso en Endpoints

### Patrón Básico

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import get_db
from app.servicios.seguridad import requiere_admin
from app.modelos import Usuario

router = APIRouter(prefix="/admin", tags=["Administración"])

@router.post("/recursos")
def crear_recurso(
    recurso: RecursoCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin)  # ✅ Validación de rol
):
    """
    Endpoint protegido por rol admin.

    Args:
        recurso: Datos del recurso a crear
        db: Sesión de base de datos (inyectada)
        admin: Usuario autenticado con rol admin (inyectado)

    Returns:
        Recurso: El recurso creado

    Raises:
        HTTPException 401: Si no está autenticado
        HTTPException 403: Si no tiene rol admin
    """
    nuevo = Recurso(**recurso.dict(), creado_por=admin.id)
    db.add(nuevo)
    db.commit()
    return nuevo
```

---

### Migración de Validación Manual

**❌ ANTES (Validación manual - código duplicado)**:

```python
@router.get("/admin/dashboard")
def obtener_dashboard(
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    # ❌ Validación manual duplicada en cada endpoint
    roles = (
        db.query(UsuarioRol.rol)
        .filter(
            UsuarioRol.usuario_id == usuario_actual.id,
            UsuarioRol.activo == True
        )
        .all()
    )

    roles_normalizados = [r[0].upper() for r in roles]

    if "ADMIN" not in roles_normalizados:
        raise HTTPException(status_code=403, detail="No autorizado")

    return obtener_estadisticas_dashboard(db)
```

**✅ AHORA (Dependency - código limpio)**:

```python
@router.get("/admin/dashboard")
def obtener_dashboard(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin)  # ✅ Dependency hace la validación
):
    """
    Obtiene estadísticas del dashboard.
    Requiere rol: admin
    """
    return obtener_estadisticas_dashboard(db)
```

**Beneficios**:
- ✅ Código más limpio y legible
- ✅ No hay duplicación de lógica
- ✅ Mensajes de error consistentes
- ✅ Logging automático
- ✅ Más fácil de mantener

---

## 🎯 Casos de Uso

### Caso 1: Endpoint Solo Admin

```python
@router.delete("/usuarios/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin)
):
    """Solo admins pueden eliminar usuarios"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404)

    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado"}
```

---

### Caso 2: Docentes Pueden Ver Sus Estudiantes

```python
@router.get("/docentes/mis-estudiantes")
def listar_mis_estudiantes(
    db: Session = Depends(get_db),
    docente: Usuario = Depends(requiere_docente)
):
    """Solo docentes pueden ver sus estudiantes"""

    # Obtener cursos del docente
    cursos = db.query(Curso).filter(Curso.docente_id == docente.id).all()

    # Obtener estudiantes de esos cursos
    estudiantes = []
    for curso in cursos:
        estudiantes.extend(curso.estudiantes)

    return estudiantes
```

---

### Caso 3: Contenido Compartido (Admin o Docente)

```python
@router.post("/contenido-educativo")
def crear_contenido_educativo(
    contenido: ContenidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente"))
):
    """
    Admins y docentes pueden crear contenido educativo.
    """
    nuevo = ContenidoLectura(
        **contenido.dict(),
        creado_por=usuario.id
    )
    db.add(nuevo)
    db.commit()
    return nuevo
```

---

### Caso 4: Ver Progreso (Múltiples Roles con Lógica Adicional)

```python
@router.get("/estudiantes/{estudiante_id}/progreso")
def ver_progreso(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente", "padre"))
):
    """
    Múltiples roles pueden ver progreso, pero con restricciones:
    - Admin: puede ver cualquier estudiante
    - Docente: solo estudiantes en sus cursos
    - Padre: solo sus hijos
    """
    roles = obtener_roles_usuario(db, usuario.id)

    if "admin" not in roles:
        # No es admin, verificar relación
        if "docente" in roles:
            # Verificar que el estudiante está en un curso del docente
            tiene_acceso = db.query(Inscripcion).join(Curso).filter(
                Inscripcion.estudiante_id == estudiante_id,
                Curso.docente_id == usuario.id
            ).first()

            if not tiene_acceso:
                raise HTTPException(
                    status_code=403,
                    detail="El estudiante no está en tus cursos"
                )

        elif "padre" in roles:
            # Verificar que el estudiante es hijo del padre
            es_hijo = db.query(PadreEstudiante).filter(
                PadreEstudiante.padre_id == usuario.id,
                PadreEstudiante.estudiante_id == estudiante_id
            ).first()

            if not es_hijo:
                raise HTTPException(
                    status_code=403,
                    detail="El estudiante no es tu hijo"
                )

    # Si llegó aquí, tiene acceso
    progreso = calcular_progreso_estudiante(db, estudiante_id)
    return progreso
```

---

### Caso 5: Superusuario (Admin + Docente)

```python
@router.get("/admin/estadisticas/avanzadas")
def estadisticas_avanzadas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_todos_los_roles("admin", "docente"))
):
    """
    Solo usuarios que son TANTO admin COMO docente pueden acceder.
    Útil para estadísticas que requieren perspectiva de ambos roles.
    """
    stats = {
        "total_estudiantes": db.query(Estudiante).count(),
        "total_docentes": db.query(Docente).count(),
        "promedio_calificaciones": calcular_promedio_global(db),
        "cursos_activos": db.query(Curso).filter(Curso.activo == True).count(),
    }
    return stats
```

---

## 📚 Mejores Prácticas

### 1. Usa la Dependency Correcta

```python
# ✅ CORRECTO - Usa dependency específica
@router.post("/admin/configuracion")
def actualizar_config(
    admin: Usuario = Depends(requiere_admin)
):
    ...

# ❌ INCORRECTO - Validación manual
@router.post("/admin/configuracion")
def actualizar_config(
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    # Validar manualmente
    if not verificar_rol(db, usuario.id, "admin"):
        raise HTTPException(...)
    ...
```

---

### 2. Nombra el Parámetro Según el Rol

```python
# ✅ CORRECTO - Nombre descriptivo
@router.get("/admin/dashboard")
def dashboard(
    admin: Usuario = Depends(requiere_admin)  # Se llama 'admin'
):
    logger.info(f"Admin {admin.email} accedió al dashboard")
    ...

# ✅ TAMBIÉN CORRECTO - Nombre genérico si hay múltiples roles
@router.get("/recursos")
def listar_recursos(
    usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente"))
):
    roles = obtener_roles_usuario(db, usuario.id)
    logger.info(f"Usuario {usuario.email} con roles {roles} listó recursos")
    ...
```

---

### 3. Documentación Clara

```python
@router.post("/contenido")
def crear_contenido(
    contenido: ContenidoCreate,
    usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente"))
):
    """
    Crea nuevo contenido educativo.

    **Roles permitidos**: admin, docente

    **Validaciones adicionales**:
    - El contenido debe tener al menos 100 palabras
    - La edad mínima debe ser entre 5 y 18 años

    Args:
        contenido: Datos del contenido a crear

    Returns:
        ContenidoLectura: El contenido creado

    Raises:
        HTTPException 401: Si no está autenticado
        HTTPException 403: Si no tiene rol admin o docente
        HTTPException 400: Si los datos son inválidos
    """
    ...
```

---

### 4. Logging de Accesos

Las dependencies ya incluyen logging automático:

```python
# Log automático cuando se PERMITE acceso
logger.debug(f"✅ Acceso admin autorizado: user@example.com")

# Log automático cuando se DENIEGA acceso
logger.warning(f"⚠️ Acceso denegado: user@example.com intentó acceder a endpoint admin sin permisos")
```

Puedes agregar logging adicional en el endpoint:

```python
@router.delete("/recursos/{recurso_id}")
def eliminar_recurso(
    recurso_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin)
):
    recurso = db.query(Recurso).filter(Recurso.id == recurso_id).first()
    if not recurso:
        raise HTTPException(status_code=404)

    # Log de la acción específica
    logger.warning(
        f"🗑️ ELIMINACIÓN: Admin {admin.email} eliminó recurso ID={recurso_id} "
        f"(nombre: {recurso.nombre})"
    )

    db.delete(recurso)
    db.commit()
    return {"mensaje": "Recurso eliminado"}
```

---

### 5. Combinar con Auditoría

Usa las dependencies de roles junto con el middleware de auditoría:

```python
from app.middlewares import get_db_with_audit_context

@router.post("/estudiantes")
def crear_estudiante(
    estudiante: EstudianteCreate,
    db: Session = Depends(get_db_with_audit_context),  # ✅ Auditoría
    admin: Usuario = Depends(requiere_admin)            # ✅ Validación de rol
):
    """
    Combina:
    - Validación de rol (solo admin puede crear)
    - Auditoría completa (quién, cuándo, desde dónde)
    """
    nuevo = Estudiante(**estudiante.dict())
    db.add(nuevo)
    db.commit()

    # La tabla auditoria tendrá:
    # - usuario_id = admin.id ✅
    # - accion = 'INSERT'
    # - tabla_afectada = 'estudiante'
    # - ip_address = request.client.host ✅

    return nuevo
```

---

## 🔍 Funciones Auxiliares

### `verificar_rol()`

Verifica si un usuario tiene un rol específico.

```python
from app.servicios.seguridad import verificar_rol

def mi_funcion_custom(db: Session, usuario_id: int):
    # Verificar si el usuario es admin
    es_admin = verificar_rol(db, usuario_id, "admin")

    if es_admin:
        # Lógica para admins
        ...
    else:
        # Lógica para no-admins
        ...
```

---

### `obtener_roles_usuario()`

Obtiene todos los roles activos de un usuario.

```python
from app.servicios.seguridad import obtener_roles_usuario

@router.get("/perfil/roles")
def mis_roles(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual)
):
    """Retorna los roles del usuario autenticado"""
    roles = obtener_roles_usuario(db, usuario.id)

    return {
        "usuario_id": usuario.id,
        "email": usuario.email,
        "roles": roles  # ['admin', 'docente']
    }
```

---

## 🐛 Troubleshooting

### Error: "Acceso denegado: se requiere rol de administrador"

**Síntomas**: HTTPException 403 al intentar acceder a endpoint admin.

**Diagnóstico**:

1. Verificar que el usuario tiene el rol asignado:
```sql
SELECT * FROM usuario_rol
WHERE usuario_id = <ID_USUARIO>
  AND rol = 'admin'
  AND activo = true;
```

2. Verificar que el token JWT es válido:
```python
# En Swagger/OpenAPI, revisa el token
# Debe tener el email correcto en el payload
```

3. Verificar logs:
```
⚠️ Acceso denegado: user@example.com intentó acceder a endpoint admin sin permisos
```

**Solución**:
```python
# Asignar rol admin al usuario
from app.servicios.seguridad import asignar_rol

db = SessionLocal()
asignar_rol(db, usuario_id=1, rol="admin")
db.close()
```

---

### Error: "HTTPException 401: No se pudieron validar las credenciales"

**Causa**: El token JWT no es válido o está expirado.

**Solución**:
1. Hacer login nuevamente para obtener nuevo token
2. Verificar que el token se envía en header: `Authorization: Bearer <token>`

---

### El usuario tiene el rol pero sigue siendo denegado

**Diagnóstico**:

Verificar que el rol está **activo**:
```sql
SELECT id, usuario_id, rol, activo, fecha_expiracion
FROM usuario_rol
WHERE usuario_id = <ID>
  AND rol = '<ROL>';
```

**Problemas comunes**:
- `activo = false` → Activar el rol
- `fecha_expiracion < NOW()` → El rol expiró, renovar

**Solución**:
```sql
-- Activar rol
UPDATE usuario_rol
SET activo = true, fecha_expiracion = NULL
WHERE id = <ROL_ID>;
```

---

### Dependency no se está ejecutando

**Síntoma**: El endpoint NO valida el rol.

**Diagnóstico**: Verificar que la dependency está correctamente declarada:

```python
# ❌ INCORRECTO - No se ejecuta
@router.get("/admin/dashboard")
def dashboard(admin = requiere_admin):  # Falta Depends()
    ...

# ✅ CORRECTO
@router.get("/admin/dashboard")
def dashboard(admin: Usuario = Depends(requiere_admin)):
    ...
```

---

## 🔒 Seguridad

### ¿Se puede falsificar un rol?

**NO**. Los roles están en la base de datos y se validan en el backend:

1. Cliente envía JWT token (solo tiene email/sub)
2. Backend valida token y obtiene usuario
3. Backend consulta roles en la BD: `SELECT * FROM usuario_rol WHERE usuario_id = ...`
4. El cliente NO puede modificar la tabla `usuario_rol`

### ¿Qué pasa si alguien modifica el payload del JWT?

El token JWT está **firmado** con `SECRET_KEY`. Si alguien modifica el payload:
- La firma no coincide
- `jwt.decode()` lanza JWTError
- La autenticación falla → 401 Unauthorized

---

## 📖 Referencias

- **Código fuente**: `app/servicios/seguridad.py`
- **Modelo**: `app/modelos/usuario_rol.py`
- **Routers ejemplo**:
  - `app/routers/admin_dashboard.py` - Usa `requiere_admin`
  - `app/routers/admin_docentes.py` - Usa `requiere_admin`
  - `app/routers/admin_estudiantes.py` - Usa `requiere_admin`

---

**Creado**: 2025-12-27
**Versión**: 2.0.0
**Sistema**: TutorIA - Backend - Validación de Roles y Autorización
