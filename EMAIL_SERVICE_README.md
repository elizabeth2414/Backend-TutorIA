# 📧 Servicio de Email - TutorIA

Documentación completa del servicio de envío de emails para reset de contraseña y notificaciones.

---

## 📑 Tabla de Contenidos

1. [Descripción General](#-descripción-general)
2. [Características](#-características)
3. [Proveedores Soportados](#-proveedores-soportados)
4. [Configuración](#-configuración)
   - [Variables de Entorno](#variables-de-entorno)
   - [Modo Desarrollo (Dev)](#1-modo-desarrollo-dev)
   - [SMTP (Gmail, Outlook, etc.)](#2-smtp-gmail-outlook-etc)
   - [SendGrid](#3-sendgrid)
5. [Uso](#-uso)
6. [Plantillas HTML](#-plantillas-html)
7. [Testing](#-testing)
8. [Troubleshooting](#-troubleshooting)
9. [Seguridad](#-seguridad)
10. [Mejoras Futuras](#-mejoras-futuras)

---

## 🎯 Descripción General

El servicio de email de TutorIA es un sistema centralizado y flexible para el envío de correos electrónicos, diseñado principalmente para:

- **Reset de contraseña**: Envío de tokens seguros para recuperación de cuenta
- **Notificaciones** (futuro): Alertas a padres, recordatorios, etc.
- **Emails transaccionales** (futuro): Confirmaciones, bienvenida, etc.

### Arquitectura

```
┌─────────────────────────────────────────────────┐
│          Servicios de la Aplicación             │
│    (auth.py, notificaciones.py, etc.)           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         app/servicios/email_service.py          │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │       EmailService (Singleton)           │   │
│  │                                           │   │
│  │  - Configuración centralizada             │   │
│  │  - Gestión de proveedores                 │   │
│  │  - Carga de plantillas HTML               │   │
│  │  - Logging completo                       │   │
│  └───────────────┬───────────────────────────┘   │
└──────────────────┼──────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
    ┌────▼────┐      ┌──────▼──────┐      ┌──────▼──────┐
    │  SMTP   │      │  SendGrid   │      │     Dev     │
    │ (Email) │      │    (API)    │      │  (Console)  │
    └─────────┘      └─────────────┘      └─────────────┘
```

---

## ✨ Características

- ✅ **Múltiples proveedores**: SMTP, SendGrid, modo desarrollo
- ✅ **Plantillas HTML**: Emails profesionales y responsive
- ✅ **Fallback a texto plano**: Compatibilidad con clientes antiguos
- ✅ **Logging completo**: Trazabilidad de todos los envíos
- ✅ **Manejo de errores robusto**: No falla la aplicación si el email falla
- ✅ **Modo desarrollo**: Imprime en consola sin enviar (ideal para testing)
- ✅ **Configuración flexible**: Vía variables de entorno
- ✅ **Variables en plantillas**: Sistema de reemplazo simple y efectivo

---

## 🔌 Proveedores Soportados

### 1. **SMTP** (Recomendado para desarrollo y startups)

**Pros:**
- ✅ Universal, funciona con cualquier servidor SMTP
- ✅ Gratis con Gmail, Outlook, etc. (con límites)
- ✅ Sin dependencias externas
- ✅ Configuración simple

**Cons:**
- ❌ Límites de envío (Gmail: 500/día)
- ❌ Riesgo de caer en spam
- ❌ Más lento que APIs nativas

**Proveedores compatibles:**
- Gmail (smtp.gmail.com)
- Outlook (smtp.office365.com)
- Yahoo (smtp.mail.yahoo.com)
- Cualquier servidor SMTP personalizado

---

### 2. **SendGrid** (Recomendado para producción)

**Pros:**
- ✅ 100 emails/día gratis (plan Free)
- ✅ API rápida y confiable
- ✅ Analíticas y tracking
- ✅ Alta deliverability (no spam)
- ✅ Escalable

**Cons:**
- ❌ Requiere cuenta y API key
- ❌ Dependencia de python-sendgrid

**Sitio web:** https://sendgrid.com

---

### 3. **Dev (Development)** (Solo desarrollo)

**Pros:**
- ✅ No requiere configuración
- ✅ No envía emails reales
- ✅ Ideal para testing local
- ✅ Imprime en consola para verificar contenido

**Cons:**
- ❌ Solo para desarrollo, NO usar en producción

---

## ⚙️ Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura según tu proveedor.

```bash
cp .env.example .env
```

#### **Variables Comunes (todos los proveedores)**

```bash
# Proveedor de email: smtp | sendgrid | dev
EMAIL_PROVIDER=dev

# Email del remitente
EMAIL_FROM=noreply@tutoria.com

# URL del frontend (para enlaces en emails)
FRONTEND_URL=http://localhost:3000

# Modo debug (True = incluye token en respuesta API, False = solo por email)
DEBUG=True
```

---

### 1. Modo Desarrollo (Dev)

**Ideal para:** Testing local, desarrollo sin configurar email real.

**Configuración mínima:**

```bash
EMAIL_PROVIDER=dev
EMAIL_FROM=noreply@tutoria.com
FRONTEND_URL=http://localhost:3000
DEBUG=True
```

**Comportamiento:**
- ✅ NO envía emails reales
- ✅ Imprime el contenido en la consola del servidor
- ✅ Retorna éxito siempre
- ✅ Token incluido en respuesta de API (si DEBUG=True)

**Ejemplo de salida en consola:**

```
================================================================================
📧 [MODO DESARROLLO] Email NO enviado (solo impreso en consola)
Para: usuario@ejemplo.com
Asunto: Resetear Contraseña - TutorIA
De: noreply@tutoria.com
--------------------------------------------------------------------------------
Contenido HTML:
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    ...
</head>
<body>
    Hola Usuario, recibimos una solicitud para resetear tu contraseña...
</body>
</html>
================================================================================
```

---

### 2. SMTP (Gmail, Outlook, etc.)

#### Opción A: Gmail (Recomendado para desarrollo)

**Paso 1: Habilitar "App Passwords" en Gmail**

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. Ve a **Seguridad** → **Verificación en 2 pasos** (habilítala si no la tienes)
3. Busca **Contraseñas de aplicaciones** (App Passwords)
4. Genera una nueva contraseña de aplicación para "Correo"
5. Copia el password generado (16 caracteres, algo como: `abcd efgh ijkl mnop`)

**Paso 2: Configurar `.env`**

```bash
EMAIL_PROVIDER=smtp
EMAIL_FROM=tu-email@gmail.com
FRONTEND_URL=http://localhost:3000

# Configuración SMTP para Gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # El App Password de 16 caracteres
SMTP_USE_TLS=True
```

**Paso 3: Probar**

Reinicia el servidor y prueba el endpoint de reset password:

```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com"}'
```

**Limitaciones de Gmail:**
- ⚠️ Máximo 500 emails por día
- ⚠️ Máximo 100 destinatarios por email
- ⚠️ Solo para desarrollo/proyectos pequeños

---

#### Opción B: Outlook/Hotmail

**Configuración `.env`:**

```bash
EMAIL_PROVIDER=smtp
EMAIL_FROM=tu-email@outlook.com
FRONTEND_URL=http://localhost:3000

# Configuración SMTP para Outlook
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=tu-email@outlook.com
SMTP_PASSWORD=tu-password-normal  # Outlook no requiere App Password
SMTP_USE_TLS=True
```

**Limitaciones de Outlook:**
- ⚠️ Máximo 300 emails por día (cuenta gratuita)
- ⚠️ Máximo 100 destinatarios por email

---

#### Opción C: Servidor SMTP Personalizado

Si tienes tu propio servidor de email o usas un proveedor empresarial:

```bash
EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@tudominio.com
FRONTEND_URL=https://app.tudominio.com

SMTP_HOST=mail.tudominio.com
SMTP_PORT=587  # O 465 para SSL directo
SMTP_USER=noreply@tudominio.com
SMTP_PASSWORD=tu-password-smtp
SMTP_USE_TLS=True  # O False si usas SSL directo en puerto 465
```

---

### 3. SendGrid

**Ideal para:** Producción, proyectos escalables.

**Paso 1: Crear cuenta en SendGrid**

1. Regístrate en https://sendgrid.com (plan Free: 100 emails/día)
2. Verifica tu email
3. Completa el onboarding

**Paso 2: Crear API Key**

1. Ve a **Settings** → **API Keys**
2. Clic en **Create API Key**
3. Nombre: `TutorIA Backend`
4. Permisos: **Full Access** (o solo **Mail Send** si prefieres restringir)
5. Copia el API Key generado (comienza con `SG.`)
   - ⚠️ **IMPORTANTE**: Solo se muestra una vez, guárdalo en lugar seguro

**Paso 3: Verificar dominio del remitente (Sender Verification)**

SendGrid requiere verificar que eres dueño del email remitente:

- **Opción A - Single Sender Verification** (más rápido):
  1. Ve a **Settings** → **Sender Authentication** → **Single Sender Verification**
  2. Agrega tu email (ej: `noreply@gmail.com`)
  3. Verifica el email de confirmación que te llega

- **Opción B - Domain Authentication** (recomendado para producción):
  1. Ve a **Settings** → **Sender Authentication** → **Authenticate Your Domain**
  2. Agrega tu dominio (ej: `tutoria.com`)
  3. Configura los registros DNS (CNAME) que te indique SendGrid
  4. Espera verificación (puede tardar 24-48 horas)

**Paso 4: Instalar dependencia Python**

```bash
pip install sendgrid
```

Agrega a `requirements.txt`:

```
sendgrid==6.11.0
```

**Paso 5: Configurar `.env`**

```bash
EMAIL_PROVIDER=sendgrid
EMAIL_FROM=noreply@tutoria.com  # Debe coincidir con el sender verificado
FRONTEND_URL=https://app.tutoria.com

# API Key de SendGrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Paso 6: Probar**

Reinicia el servidor y prueba el endpoint:

```bash
curl -X POST https://api.tutoria.com/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com"}'
```

**Ventajas de SendGrid:**
- ✅ 100 emails/día gratis (suficiente para MVP)
- ✅ Hasta 40,000 emails/día en plan Essentials ($19.95/mes)
- ✅ Analíticas: open rate, click rate, bounces
- ✅ Deliverability superior (menos spam)
- ✅ API rápida (no SMTP)

---

## 🚀 Uso

### Desde el código Python

```python
from app.servicios.email_service import email_service

# Enviar email de reset de contraseña
email_service.send_reset_password_email(
    to_email="usuario@ejemplo.com",
    usuario_nombre="Juan Pérez",
    reset_token="abc123xyz789"
)

# Enviar email personalizado
email_service.send_email(
    to_email="usuario@ejemplo.com",
    subject="Bienvenido a TutorIA",
    html_content="<h1>Hola!</h1><p>Gracias por registrarte.</p>",
    text_content="Hola! Gracias por registrarte."  # Fallback
)
```

### Desde el endpoint de reset password

El servicio ya está integrado en `POST /auth/reset-password`:

```bash
# Solicitar reset
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com"}'

# Respuesta (modo DEBUG=True):
{
  "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
  "email": "usuario@ejemplo.com",
  "debug_token": "abc123xyz789",  # ⚠️ Solo en DEBUG=True
  "debug_expires": "2024-01-15T14:30:00"
}
```

---

## 📝 Plantillas HTML

### Ubicación

Las plantillas están en `app/templates/`:

```
app/
├── templates/
│   └── email_reset_password.html  # Plantilla de reset de contraseña
```

### Variables Disponibles

Las plantillas usan un sistema simple de reemplazo con `{{VARIABLE}}`:

```html
<!DOCTYPE html>
<html>
<body>
    <h1>Hola {{USUARIO_NOMBRE}},</h1>
    <p>Haz clic en el enlace para resetear tu contraseña:</p>
    <a href="{{RESET_URL}}">Resetear Contraseña</a>

    <p>Token manual: {{TOKEN}}</p>
    <p>Ir a la app: {{FRONTEND_URL}}</p>
</body>
</html>
```

**Variables predefinidas:**
- `{{USUARIO_NOMBRE}}` - Nombre del usuario
- `{{RESET_URL}}` - URL completa con token (ej: `http://localhost:3000/reset-password?token=abc123`)
- `{{TOKEN}}` - Token sin URL (ej: `abc123xyz789`)
- `{{FRONTEND_URL}}` - URL base del frontend

### Crear nuevas plantillas

**Paso 1: Crear archivo HTML**

```bash
touch app/templates/email_bienvenida.html
```

**Paso 2: Diseñar email**

```html
<!DOCTYPE html>
<html lang="es">
<body>
    <h1>¡Bienvenido {{USUARIO_NOMBRE}}!</h1>
    <p>Gracias por unirte a TutorIA.</p>
</body>
</html>
```

**Paso 3: Agregar método en EmailService**

```python
# En app/servicios/email_service.py

def send_welcome_email(self, to_email: str, usuario_nombre: str) -> bool:
    template = self._load_template('email_bienvenida.html')

    html_content = template.replace('{{USUARIO_NOMBRE}}', usuario_nombre)

    return self.send_email(
        to_email=to_email,
        subject="Bienvenido a TutorIA",
        html_content=html_content
    )
```

---

## 🧪 Testing

### Test Manual - Modo Dev

1. Configurar en `.env`:
   ```bash
   EMAIL_PROVIDER=dev
   DEBUG=True
   ```

2. Ejecutar servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Probar endpoint:
   ```bash
   curl -X POST http://localhost:8000/auth/reset-password \
     -H "Content-Type: application/json" \
     -d '{"email": "test@ejemplo.com"}'
   ```

4. Verificar en la consola del servidor que se imprime el email

---

### Test Manual - SMTP (Gmail)

1. Configurar Gmail en `.env` (ver sección de configuración)

2. Probar con tu propio email:
   ```bash
   curl -X POST http://localhost:8000/auth/reset-password \
     -H "Content-Type: application/json" \
     -d '{"email": "tu-email@gmail.com"}'
   ```

3. Verificar que llegue el email a tu bandeja de entrada

---

### Test Manual - SendGrid

1. Configurar SendGrid en `.env`

2. Probar con un email verificado:
   ```bash
   curl -X POST http://localhost:8000/auth/reset-password \
     -H "Content-Type: application/json" \
     -d '{"email": "email-verificado@ejemplo.com"}'
   ```

3. Verificar en el dashboard de SendGrid:
   - Ve a **Activity** para ver el envío
   - Estado: Delivered, Bounced, etc.

---

### Test Unitario (pytest)

Crear archivo `tests/test_email_service.py`:

```python
import pytest
from app.servicios.email_service import EmailService
from app import settings

def test_email_service_dev_mode():
    """Test que el modo dev no falla"""
    settings.EMAIL_PROVIDER = 'dev'
    service = EmailService()

    result = service.send_reset_password_email(
        to_email="test@ejemplo.com",
        usuario_nombre="Test User",
        reset_token="abc123"
    )

    assert result == True

def test_email_service_invalid_provider():
    """Test que un proveedor inválido retorna False"""
    settings.EMAIL_PROVIDER = 'invalid'
    service = EmailService()

    result = service.send_email(
        to_email="test@ejemplo.com",
        subject="Test",
        html_content="<p>Test</p>"
    )

    assert result == False
```

Ejecutar:

```bash
pytest tests/test_email_service.py -v
```

---

## 🔧 Troubleshooting

### Problema 1: Email no llega (SMTP)

**Síntomas:**
- El código no lanza errores
- Logs dicen "Email enviado exitosamente"
- Pero el email no llega

**Soluciones:**

1. **Verificar carpeta de spam**
   - Los emails SMTP tienen alta probabilidad de ir a spam

2. **Verificar configuración SMTP**
   ```bash
   # Probar conexión SMTP manualmente con telnet:
   telnet smtp.gmail.com 587
   ```

3. **Verificar App Password (Gmail)**
   - Asegúrate de usar App Password, NO tu contraseña normal
   - Regenera el App Password si no funciona

4. **Verificar límites de envío**
   - Gmail: 500/día
   - Outlook: 300/día

5. **Revisar logs del servidor**
   ```bash
   tail -f logs/tutoria.log | grep "Email"
   ```

---

### Problema 2: Error "Authentication failed" (SMTP)

**Síntomas:**
```
❌ Error al enviar email SMTP a usuario@ejemplo.com:
(535, b'5.7.8 Username and Password not accepted.')
```

**Soluciones:**

1. **Gmail**: Verificar que estés usando App Password
   - No uses tu contraseña normal de Gmail
   - Genera un nuevo App Password

2. **Verificar credenciales en `.env`**
   ```bash
   SMTP_USER=tu-email@gmail.com  # ¿Correcto?
   SMTP_PASSWORD=abcd efgh ijkl mnop  # ¿Es el App Password?
   ```

3. **Verificar 2FA habilitado** (Gmail)
   - Gmail requiere verificación en 2 pasos para App Passwords

---

### Problema 3: Error "SENDGRID_API_KEY no configurada"

**Síntomas:**
```
❌ SENDGRID_API_KEY no configurada. Verifica .env
```

**Soluciones:**

1. Verificar que la variable esté en `.env`:
   ```bash
   cat .env | grep SENDGRID_API_KEY
   ```

2. Verificar que el API Key sea correcto:
   - Comienza con `SG.`
   - Tiene ~69 caracteres
   - No tiene espacios ni saltos de línea

3. Reiniciar el servidor después de cambiar `.env`

---

### Problema 4: Error "Módulo sendgrid no instalado"

**Síntomas:**
```
❌ Módulo sendgrid no instalado. Ejecuta: pip install sendgrid
```

**Soluciones:**

1. Instalar la dependencia:
   ```bash
   pip install sendgrid
   ```

2. Agregar a `requirements.txt`:
   ```
   sendgrid==6.11.0
   ```

3. Reiniciar el servidor

---

### Problema 5: Email cae en spam (SMTP)

**Síntomas:**
- El email llega, pero a la carpeta de spam

**Soluciones:**

1. **Usar SendGrid** (deliverability superior)
   - Las APIs dedicadas tienen mejor reputación

2. **Configurar SPF/DKIM** (avanzado)
   - Requiere acceso a DNS de tu dominio
   - Solo útil si envías desde tu dominio (no Gmail)

3. **Mejorar contenido del email**
   - Evitar palabras spam: "gratis", "urgente", "haz clic aquí"
   - Incluir botón de "unsubscribe" (futuro)
   - Texto plano + HTML (ya implementado)

4. **Verificar dominio remitente**
   - Si usas `noreply@tutoria.com`, asegúrate de que `tutoria.com` sea tuyo

---

## 🔒 Seguridad

### Mejores Prácticas

#### 1. **Nunca commitear credenciales**

❌ **MAL:**
```python
# En el código
SMTP_PASSWORD = "mi-password-secreta"
```

✅ **BIEN:**
```python
# En .env (ignorado por git)
SMTP_PASSWORD=mi-password-secreta

# En el código
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
```

---

#### 2. **Usar variables de entorno en producción**

En producción (Heroku, AWS, etc.), NO uses archivo `.env`. Usa variables de entorno del sistema:

```bash
# Heroku
heroku config:set EMAIL_PROVIDER=sendgrid
heroku config:set SENDGRID_API_KEY=SG.xxx

# AWS Elastic Beanstalk
eb setenv EMAIL_PROVIDER=sendgrid SENDGRID_API_KEY=SG.xxx

# Docker
docker run -e EMAIL_PROVIDER=sendgrid -e SENDGRID_API_KEY=SG.xxx
```

---

#### 3. **Modo DEBUG=False en producción**

⚠️ **CRÍTICO**: En producción, el token NO debe incluirse en la respuesta de la API.

```bash
# .env en producción
DEBUG=False
```

Con `DEBUG=False`, la respuesta es:

```json
{
  "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
  "email": "usuario@ejemplo.com"
}
```

**Sin** `debug_token` ni `debug_expires`.

---

#### 4. **Rate Limiting**

Implementar límite de solicitudes para evitar abuso:

```python
# Futuro: Agregar rate limiting
# Ejemplo con slowapi:
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/reset-password")
@limiter.limit("3/hour")  # Máximo 3 solicitudes por hora por IP
def reset_password(...):
    ...
```

---

#### 5. **Validar email antes de enviar**

Ya implementado:

```python
# En resetear_password()
usuario = db.query(Usuario).filter(Usuario.email == email).first()

if not usuario:
    # ✅ No revelamos si el email existe
    return {"mensaje": "Si el email existe..."}
```

---

#### 6. **Proteger API Keys**

- ✅ Usar variables de entorno
- ✅ Nunca loggear API Keys completos
- ✅ Rotar API Keys periódicamente (cada 3-6 meses)
- ✅ Usar permisos mínimos (SendGrid: solo "Mail Send")

---

#### 7. **HTTPS en producción**

⚠️ **CRÍTICO**: Los enlaces de reset DEBEN usar HTTPS en producción:

```bash
# .env en producción
FRONTEND_URL=https://app.tutoria.com  # ✅ HTTPS
```

---

## 🚀 Mejoras Futuras

### Funcionalidades Pendientes

1. **Email de bienvenida**
   - Al registrarse un nuevo usuario
   - Plantilla: `email_bienvenida.html`

2. **Notificaciones a padres**
   - Cuando hijo completa una actividad
   - Cuando hijo sube de nivel
   - Plantilla: `email_notificacion_padre.html`

3. **Emails programados**
   - Recordatorios semanales
   - Resumen mensual de progreso
   - Usar Celery + Redis para scheduling

4. **Email tracking**
   - Guardar en BD todos los emails enviados
   - Tabla: `email_log`
   - Campos: destinatario, asunto, estado, fecha

5. **Soporte para adjuntos**
   - Reportes PDF
   - Certificados
   - Usar `MIMEMultipart` con attachments

6. **Internacionalización (i18n)**
   - Plantillas en español e inglés
   - Detección automática de idioma del usuario

7. **Más proveedores**
   - Amazon SES
   - Mailgun
   - Postmark

8. **Testing automatizado**
   - Mock de SMTP en tests
   - Tests de integración con SendGrid sandbox

9. **Rate limiting**
   - Límite por IP
   - Límite por usuario
   - Usar slowapi o Redis

10. **Analytics**
    - Dashboard de emails enviados
    - Tasas de apertura (SendGrid)
    - Tasas de clic

---

## 📊 Comparación de Proveedores

| Característica        | Dev       | SMTP (Gmail) | SendGrid Free | SendGrid Paid |
|-----------------------|-----------|--------------|---------------|---------------|
| **Emails/día**        | Ilimitado | 500          | 100           | 40,000+       |
| **Costo**             | Gratis    | Gratis       | Gratis        | $19.95/mes    |
| **Velocidad**         | Instantáneo | Lento (~2s)  | Rápido (~0.5s)| Rápido        |
| **Deliverability**    | N/A       | Media (spam) | Alta          | Muy alta      |
| **Analytics**         | No        | No           | Sí            | Sí (avanzado) |
| **Configuración**     | Ninguna   | Media        | Media         | Media         |
| **Ideal para**        | Desarrollo| Desarrollo   | MVP           | Producción    |

---

## 📚 Referencias

- **Documentación SendGrid**: https://docs.sendgrid.com/
- **Gmail App Passwords**: https://support.google.com/accounts/answer/185833
- **SMTP RFC**: https://tools.ietf.org/html/rfc5321
- **Email HTML Best Practices**: https://www.campaignmonitor.com/css/
- **MIME Types**: https://tools.ietf.org/html/rfc2045

---

## 🎓 Conclusión

El servicio de email de TutorIA está diseñado para ser:

- ✅ **Flexible**: Múltiples proveedores
- ✅ **Escalable**: Desde dev hasta producción
- ✅ **Robusto**: Manejo de errores completo
- ✅ **Seguro**: Mejores prácticas implementadas
- ✅ **Fácil de usar**: API simple y clara

**Recomendaciones por fase:**

1. **Desarrollo local**: Usar `dev` mode
2. **Testing con emails reales**: Usar SMTP (Gmail)
3. **MVP/Beta**: Usar SendGrid Free (100 emails/día)
4. **Producción**: Usar SendGrid Paid o Amazon SES

---

**¿Preguntas o problemas?**

Si encuentras bugs o necesitas ayuda, verifica:
1. Esta documentación
2. Los logs del servidor (`logs/tutoria.log`)
3. La sección de troubleshooting

**Siguiente paso**: Probar el flujo completo de reset de contraseña end-to-end.
