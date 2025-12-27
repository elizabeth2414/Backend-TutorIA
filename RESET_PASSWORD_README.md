# 🔑 Sistema de Reset de Contraseña TutorIA

Documentación completa del sistema de recuperación de contraseña ("Olvidé mi contraseña").

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Arquitectura](#arquitectura)
3. [Flujo Completo](#flujo-completo)
4. [Endpoints API](#endpoints-api)
5. [Modelos de Datos](#modelos-de-datos)
6. [Seguridad](#seguridad)
7. [Configuración](#configuración)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El sistema de reset de contraseña permite a los usuarios recuperar el acceso a su cuenta cuando olvidan su contraseña.

### Características

- ✅ **Tokens seguros**: Generados con `secrets.token_urlsafe()` (43 caracteres)
- ✅ **Expiración automática**: Tokens válidos por 1 hora
- ✅ **Un solo uso**: Cada token solo puede usarse una vez
- ✅ **No revela información**: No indica si un email existe o no
- ✅ **Tracking de seguridad**: Guarda IP del solicitante
- ✅ **Limpieza automática**: Invalida tokens anteriores al generar uno nuevo
- ✅ **Validaciones robustas**: Verifica expiración, uso previo, requisitos de contraseña
- ✅ **Logging completo**: Registra todos los eventos de seguridad

---

## 🏗️ Arquitectura

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                               │
└────────────────────────┬────────────────────────────────────┘
                         │ 1. "Olvidé mi contraseña"
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    POST /auth/reset-password                 │
│  Body: { "email": "user@example.com" }                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              resetear_password(db, email, ip)                │
│                                                              │
│  1. Busca usuario por email                                 │
│  2. Si existe:                                              │
│     - Invalida tokens anteriores no usados                  │
│     - Genera token: secrets.token_urlsafe(32)              │
│     - Guarda en BD con expiración = NOW() + 1 hora         │
│     - (TODO) Envía email con token                         │
│  3. Retorna mensaje genérico (siempre el mismo)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  USUARIO RECIBE EMAIL                        │
│  "Haz clic aquí para resetear tu contraseña:                │
│   https://app.com/reset?token=ABC123..."                    │
└────────────────────────┬────────────────────────────────────┘
                         │ 2. Clic en enlace
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               FRONTEND: Formulario Nueva Contraseña          │
└────────────────────────┬────────────────────────────────────┘
                         │ 3. Envía nueva contraseña
                         ↓
┌─────────────────────────────────────────────────────────────┐
│            POST /auth/confirm-reset-password                 │
│  Body: {                                                     │
│    "token": "ABC123...",                                    │
│    "nuevo_password": "nuevaPassword123"                     │
│  }                                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│      confirmar_reset_password(db, token, nueva_pwd)          │
│                                                              │
│  1. Busca token en BD                                       │
│  2. Valida: no usado, no expirado, existe                   │
│  3. Hashea nueva contraseña                                 │
│  4. Actualiza usuario.password_hash                         │
│  5. Marca token como usado                                  │
│  6. Invalida otros tokens del usuario                       │
│  7. Commit y retorna éxito                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│           ✅ CONTRASEÑA CAMBIADA EXITOSAMENTE               │
│              Usuario puede hacer login                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌊 Flujo Completo

### Paso 1: Usuario Solicita Reset

**Frontend**:
```javascript
// Formulario "Olvidé mi contraseña"
const response = await fetch('/auth/reset-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'usuario@example.com'
  })
});

const data = await response.json();
console.log(data.mensaje);
// "Si el email existe, se enviarán instrucciones para resetear la contraseña"
```

**Backend**:
```python
# app/servicios/auth.py
def resetear_password(db, email, ip_address):
    # 1. Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        # No revelar que el email no existe
        return {"mensaje": "Si el email existe..."}

    # 2. Invalidar tokens anteriores
    ...

    # 3. Generar nuevo token
    token = secrets.token_urlsafe(32)

    # 4. Guardar en BD
    reset_token = PasswordResetToken(
        usuario_id=usuario.id,
        token=token,
        fecha_expiracion=datetime.utcnow() + timedelta(hours=1),
        usado=False,
        ip_solicitante=ip_address
    )
    db.add(reset_token)
    db.commit()

    # 5. TODO: Enviar email
    # send_email(
    #     to=usuario.email,
    #     subject="Resetear Contraseña - TutorIA",
    #     body=f"Token: {token}"
    # )

    return {"mensaje": "Si el email existe..."}
```

---

### Paso 2: Usuario Recibe Email

**Email (Plantilla):**
```html
Hola {{usuario.nombre}},

Recibimos una solicitud para resetear tu contraseña.

Si fuiste tú, haz clic en el siguiente enlace:
https://tutoria.com/reset-password?token={{token}}

Este enlace expira en 1 hora.

Si no solicitaste esto, ignora este email.

Saludos,
Equipo TutorIA
```

---

### Paso 3: Usuario Envía Nueva Contraseña

**Frontend**:
```javascript
// Formulario con nueva contraseña
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

const response = await fetch('/auth/confirm-reset-password', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    token: token,
    nuevo_password: 'MiNuevaPassword123'
  })
});

if (response.ok) {
  const data = await response.json();
  // Redirigir a login
  window.location.href = '/login?reset=success';
} else {
  const error = await response.json();
  alert(error.detail); // "Token expirado", "Token inválido", etc.
}
```

**Backend**:
```python
# app/servicios/auth.py
def confirmar_reset_password(db, token, nuevo_password):
    # 1. Buscar token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()

    if not reset_token:
        raise HTTPException(400, "Token inválido")

    # 2. Validar que no esté usado
    if reset_token.usado:
        raise HTTPException(400, "Token ya usado")

    # 3. Validar que no esté expirado
    if reset_token.fecha_expiracion < datetime.utcnow():
        raise HTTPException(400, "Token expirado")

    # 4. Obtener usuario y cambiar contraseña
    usuario = db.query(Usuario).filter(
        Usuario.id == reset_token.usuario_id
    ).first()

    usuario.password_hash = obtener_password_hash(nuevo_password)

    # 5. Marcar token como usado
    reset_token.usado = True
    reset_token.fecha_uso = datetime.utcnow()

    # 6. Invalidar otros tokens
    ...

    db.commit()

    return {"mensaje": "Contraseña restablecida correctamente"}
```

---

## 📡 Endpoints API

### POST /auth/reset-password

Solicita un token de reset de contraseña.

**Request**:
```json
POST /auth/reset-password
Content-Type: application/json

{
  "email": "usuario@example.com"
}
```

**Response** (siempre la misma, exista o no el email):
```json
{
  "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
  "email": "usuario@example.com"
}
```

**Response en modo DEBUG** (solo desarrollo):
```json
{
  "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
  "email": "usuario@example.com",
  "debug_token": "rQ2x7Kz...pL9mN3vB",
  "debug_expires": "2025-12-27T12:30:00"
}
```

**Notas**:
- ⚠️ En producción, NUNCA incluir el token en la respuesta
- El token solo debe enviarse por email
- La IP del cliente se guarda automáticamente

---

### POST /auth/confirm-reset-password

Confirma el reset y cambia la contraseña.

**Request**:
```json
POST /auth/confirm-reset-password
Content-Type: application/json

{
  "token": "rQ2x7Kz...pL9mN3vB",
  "nuevo_password": "MiNuevaPassword123"
}
```

**Response 200** (éxito):
```json
{
  "mensaje": "Contraseña restablecida correctamente. Ya puedes iniciar sesión con tu nueva contraseña.",
  "email": "usuario@example.com"
}
```

**Response 400** (error):
```json
{
  "detail": "Token de reset inválido o expirado"
}
// O
{
  "detail": "Este token de reset ya fue utilizado"
}
// O
{
  "detail": "El token de reset ha expirado. Solicita uno nuevo."
}
// O
{
  "detail": "La contraseña debe tener al menos 8 caracteres"
}
```

---

## 💾 Modelos de Datos

### PasswordResetToken

```python
# app/modelos/password_reset_token.py
class PasswordResetToken(Base):
    __tablename__ = 'password_reset_token'

    id = Column(BigInteger, primary_key=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'))
    token = Column(String(255), unique=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    fecha_uso = Column(DateTime(timezone=True), nullable=True)
    ip_solicitante = Column(String(50), nullable=True)

    usuario = relationship("Usuario", backref="password_reset_tokens")
```

**Campos**:
- `token`: String único de 43 caracteres generado con `secrets.token_urlsafe(32)`
- `fecha_expiracion`: Normalmente `fecha_creacion + 1 hora`
- `usado`: Marca si el token ya fue utilizado (un solo uso)
- `fecha_uso`: Timestamp de cuándo se usó el token
- `ip_solicitante`: IP del cliente que solicitó el reset (para auditoría)

---

## 🔒 Seguridad

### 1. Tokens Criptográficamente Seguros

```python
import secrets

# Genera 32 bytes aleatorios, codificados en base64 URL-safe
token = secrets.token_urlsafe(32)
# Resultado: "rQ2x7KzP4mL9nN3vB8cF6dG2hJ5kL1mN0pQ3rS8tU9vW2xY5zA7"
# Longitud: 43 caracteres
# Espacio de búsqueda: 256^32 = 2^256 combinaciones posibles
```

**Propiedades**:
- URL-safe: Puede usarse directamente en URLs sin encoding
- Criptográficamente seguro: No predecible ni reproducible
- Imposible de adivinar: 2^256 combinaciones

---

### 2. No Revelar Información

**❌ MAL** (revela si email existe):
```json
// Email no existe
{
  "error": "Email no encontrado"
}

// Email existe
{
  "mensaje": "Email enviado"
}
```

**✅ BIEN** (mismo mensaje siempre):
```json
// Email existe O no existe (mismo mensaje)
{
  "mensaje": "Si el email existe, se enviarán instrucciones..."
}
```

**Razón**: Previene enumeración de usuarios. Un atacante no puede descubrir qué emails están registrados.

---

### 3. Expiración Temporal

Tokens válidos por **1 hora**:

```python
reset_token = PasswordResetToken(
    usuario_id=usuario.id,
    token=token_value,
    fecha_expiracion=datetime.utcnow() + timedelta(hours=1),  # 1 hora
    usado=False
)
```

**Balance**:
- ⏰ Suficiente tiempo para que el usuario revise su email y actúe
- 🔒 Suficientemente corto para minimizar ventana de ataque

---

### 4. Un Solo Uso

```python
# Validar que no esté usado
if reset_token.usado:
    raise HTTPException(400, "Este token ya fue utilizado")

# Después de usar, marcar como usado
reset_token.usado = True
reset_token.fecha_uso = datetime.utcnow()
```

**Previene**:
- Reutilización del mismo token
- Ataques de replay

---

### 5. Invalidación de Tokens Anteriores

```python
# Al generar un nuevo token, invalidar anteriores no usados
tokens_anteriores = db.query(PasswordResetToken).filter(
    PasswordResetToken.usuario_id == usuario.id,
    PasswordResetToken.usado == False,
    PasswordResetToken.fecha_expiracion > datetime.utcnow()
).all()

for token_anterior in tokens_anteriores:
    token_anterior.usado = True
```

**Previene**:
- Múltiples tokens activos simultáneamente
- Confusión del usuario
- Ventana de ataque reducida

---

### 6. Tracking de IP

```python
reset_token = PasswordResetToken(
    usuario_id=usuario.id,
    token=token_value,
    ip_solicitante=ip_address  # IP del solicitante
)
```

**Usos**:
- Auditoría de seguridad
- Detectar patrones de abuso
- Geolocalización de solicitudes sospechosas

---

### 7. Validación de Contraseña

```python
# Requisito mínimo: 8 caracteres
if len(nuevo_password) < 8:
    raise HTTPException(400, "La contraseña debe tener al menos 8 caracteres")
```

**Puedes agregar más requisitos**:
```python
import re

def validar_password(password):
    if len(password) < 8:
        return False, "Mínimo 8 caracteres"

    if not re.search(r"[A-Z]", password):
        return False, "Debe contener al menos una mayúscula"

    if not re.search(r"[a-z]", password):
        return False, "Debe contener al menos una minúscula"

    if not re.search(r"\d", password):
        return False, "Debe contener al menos un número"

    return True, "OK"
```

---

## ⚙️ Configuración

### Variables de Entorno

**`.env`**:
```bash
# Modo debug (muestra token en respuesta)
DEBUG=True  # ⚠️ Cambiar a False en producción

# Configuración de email (TODO)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@tutoria.com
SMTP_PASSWORD=secret_password
SMTP_FROM=TutorIA <noreply@tutoria.com>
```

---

### Configurar Servicio de Email

**Opción 1: SMTP (Gmail, Outlook, etc.)**

```python
# app/servicios/email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email_reset(email_destinatario: str, token: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Resetear Contraseña - TutorIA"
    msg['From'] = settings.SMTP_FROM
    msg['To'] = email_destinatario

    # Cuerpo del email
    html = f"""
    <html>
      <body>
        <h2>Resetear Contraseña</h2>
        <p>Recibimos una solicitud para resetear tu contraseña.</p>
        <p>
          <a href="https://tutoria.com/reset-password?token={token}">
            Haz clic aquí para resetear tu contraseña
          </a>
        </p>
        <p>Este enlace expira en 1 hora.</p>
        <p>Si no solicitaste esto, ignora este email.</p>
      </body>
    </html>
    """

    part = MIMEText(html, 'html')
    msg.attach(part)

    # Enviar
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
```

**Opción 2: SendGrid**

```python
# pip install sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def enviar_email_reset(email_destinatario: str, token: str):
    message = Mail(
        from_email='noreply@tutoria.com',
        to_emails=email_destinatario,
        subject='Resetear Contraseña - TutorIA',
        html_content=f"""
        <h2>Resetear Contraseña</h2>
        <p><a href="https://tutoria.com/reset-password?token={token}">
          Resetear mi contraseña
        </a></p>
        """
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
```

**Integrar en `resetear_password()`**:

```python
def resetear_password(db: Session, email: str, ip_address: str = None):
    # ... código existente ...

    # Enviar email con el token
    try:
        enviar_email_reset(usuario.email, token_value)
        logger.info(f"📧 Email de reset enviado a {usuario.email}")
    except Exception as e:
        logger.error(f"❌ Error al enviar email: {str(e)}")
        # No fallar la operación si el email falla
        # El token ya está en la BD

    # Retornar sin el token (ya se envió por email)
    return {
        "mensaje": "Si el email existe, se enviarán instrucciones...",
        "email": email
    }
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Flujo Completo desde Python

```python
from app.servicios.auth import resetear_password, confirmar_reset_password
from app.config import SessionLocal

db = SessionLocal()

# 1. Usuario solicita reset
resultado = resetear_password(
    db=db,
    email="usuario@example.com",
    ip_address="192.168.1.100"
)
print(resultado)
# {
#   "mensaje": "Si el email existe...",
#   "debug_token": "ABC123..."  # Solo en modo DEBUG
# }

# Simular que el usuario recibió el email y tiene el token
token = resultado["debug_token"]

# 2. Usuario envía nueva contraseña
resultado_reset = confirmar_reset_password(
    db=db,
    token=token,
    nuevo_password="NuevaPassword123"
)
print(resultado_reset)
# {
#   "mensaje": "Contraseña restablecida correctamente...",
#   "email": "usuario@example.com"
# }

db.close()
```

---

### Ejemplo 2: Testing con cURL

```bash
# 1. Solicitar reset
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@example.com"}'

# Respuesta:
# {
#   "mensaje": "Si el email existe, se enviarán instrucciones...",
#   "debug_token": "rQ2x7Kz...pL9mN3vB"
# }

# 2. Confirmar con el token recibido
curl -X POST http://localhost:8000/auth/confirm-reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "rQ2x7Kz...pL9mN3vB",
    "nuevo_password": "MiNuevaPassword123"
  }'

# Respuesta:
# {
#   "mensaje": "Contraseña restablecida correctamente...",
#   "email": "usuario@example.com"
# }
```

---

### Ejemplo 3: Verificar Token en la BD

```sql
-- Ver token generado
SELECT
    prt.id,
    u.email,
    prt.token,
    prt.fecha_creacion,
    prt.fecha_expiracion,
    prt.usado,
    prt.ip_solicitante,
    CASE
        WHEN prt.fecha_expiracion < NOW() THEN 'EXPIRADO'
        WHEN prt.usado THEN 'USADO'
        ELSE 'ACTIVO'
    END AS estado
FROM password_reset_token prt
JOIN usuario u ON prt.usuario_id = u.id
WHERE u.email = 'usuario@example.com'
ORDER BY prt.fecha_creacion DESC
LIMIT 1;
```

---

## 🐛 Troubleshooting

### Error: "Token de reset inválido o expirado"

**Causas**:
1. Token no existe en la BD
2. Token ya fue usado
3. Token expiró (> 1 hora)

**Diagnóstico**:
```sql
SELECT * FROM password_reset_token WHERE token = 'ABC123...';
```

**Solución**: Solicitar un nuevo token.

---

### Error: "Este token de reset ya fue utilizado"

**Causa**: El token ya fue usado anteriormente.

**Diagnóstico**:
```sql
SELECT usado, fecha_uso
FROM password_reset_token
WHERE token = 'ABC123...';
```

**Solución**: Solicitar un nuevo token.

---

### Error: "El token de reset ha expirado"

**Causa**: Han pasado más de 1 hora desde que se generó el token.

**Diagnóstico**:
```sql
SELECT
    fecha_creacion,
    fecha_expiracion,
    NOW() AS ahora,
    fecha_expiracion < NOW() AS expirado
FROM password_reset_token
WHERE token = 'ABC123...';
```

**Solución**: Solicitar un nuevo token.

---

### El email no llega

**Causas**:
1. Configuración SMTP incorrecta
2. Email en carpeta de spam
3. Servicio de email deshabilitado

**Diagnóstico**:
```python
# Verificar logs
logger.info("📧 Email de reset enviado...")
logger.error("❌ Error al enviar email...")
```

**Solución**:
- Verificar credenciales SMTP en `.env`
- Revisar carpeta de spam
- Probar con otro proveedor de email

---

### En modo DEBUG no se muestra el token

**Causa**: Variable `DEBUG` no está configurada correctamente.

**Solución**:
```python
# app/settings.py
class Settings(BaseSettings):
    DEBUG: bool = False  # Cambiar a True para desarrollo
```

O en `.env`:
```bash
DEBUG=True
```

---

## 📖 Referencias

- **Código fuente**:
  - Modelo: `app/modelos/password_reset_token.py`
  - Servicio: `app/servicios/auth.py`
  - Router: `app/routers/auth.py`
  - Schemas: `app/esquemas/auth.py`
- **Migración SQL**: `migrations/crear_tabla_password_reset_token.sql`
- **Estándares**: [OWASP Password Reset Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)

---

**Creado**: 2025-12-27
**Versión**: 1.0.0
**Sistema**: TutorIA - Backend - Reset de Contraseña
