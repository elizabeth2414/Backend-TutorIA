# 🔐 Configuración de Variables de Entorno

Guía completa para configurar las variables de entorno del Backend TutorIA.

---

## 📋 Índice

1. [Configuración Rápida](#configuración-rápida)
2. [Variables Requeridas](#variables-requeridas)
3. [Variables Opcionales](#variables-opcionales)
4. [Generar SECRET_KEY Segura](#generar-secret_key-segura)
5. [Configuración por Entorno](#configuración-por-entorno)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Configuración Rápida

### 1. Copiar el archivo de ejemplo

```bash
cp .env.example .env
```

### 2. Generar SECRET_KEY segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Editar el archivo `.env`

Abre `.env` y configura al menos:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/tutoria
SECRET_KEY=tu-clave-generada-en-paso-2
```

### 4. Verificar configuración

```bash
python -c "from app.settings import settings; print('✅ Configuración cargada correctamente')"
```

---

## ⚠️ Variables REQUERIDAS

Estas variables **DEBEN** estar configuradas o la aplicación NO iniciará:

### 1. `DATABASE_URL`

**Descripción**: URL de conexión a PostgreSQL

**Formato**:
```
postgresql://usuario:password@host:puerto/nombre_bd
```

**Ejemplos**:
```env
# Desarrollo local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tutoria

# Producción
DATABASE_URL=postgresql://user:pass@db.example.com:5432/tutoria_prod

# Con parámetros adicionales
DATABASE_URL=postgresql://user:pass@localhost:5432/tutoria?sslmode=require
```

**Notas**:
- El usuario debe tener permisos de CREATE, SELECT, INSERT, UPDATE, DELETE
- La base de datos debe existir previamente
- Soporta SSL con `?sslmode=require`

---

### 2. `SECRET_KEY`

**Descripción**: Clave secreta para firmar tokens JWT

**⚠️ CRÍTICO**: Esta clave debe ser:
- **Única** por instalación
- **Larga** (mínimo 32 caracteres)
- **Aleatoria** (generada criptográficamente)
- **Secreta** (NUNCA compartir o subir al repositorio)

**Cómo generar**:

```bash
# Opción 1: Python (recomendado)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opción 2: OpenSSL
openssl rand -base64 32

# Opción 3: Linux/Mac
head -c 32 /dev/urandom | base64
```

**Ejemplo**:
```env
SECRET_KEY=Dqvh1UKpy0oWxfTTWuIbl6waTyEcvvNco0XARguGBDw
```

**Notas**:
- Si cambias esta clave, todos los tokens JWT actuales se invalidarán
- Guárdala en un gestor de secretos en producción (AWS Secrets Manager, Vault, etc.)
- NUNCA uses valores por defecto en producción

---

## 🔧 Variables OPCIONALES

Estas variables tienen valores por defecto pero pueden ser personalizadas:

### Seguridad JWT

```env
# Algoritmo de firma JWT (default: HS256)
ALGORITHM=HS256

# Tiempo de expiración del token en minutos (default: 60)
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

### Servidor

```env
# Host del servidor (default: 0.0.0.0)
HOST=0.0.0.0

# Puerto del servidor (default: 8000)
PORT=8000

# Entorno de ejecución (default: development)
ENVIRONMENT=production
```

---

### IA y Modelos

```env
# Modelo de Whisper para transcripción (default: small)
# Opciones: tiny, base, small, medium, large
WHISPER_MODEL=small
```

**Comparación de modelos**:

| Modelo | Tamaño | RAM | Precisión | Velocidad |
|--------|--------|-----|-----------|-----------|
| tiny   | ~75 MB | ~1 GB | Baja | Muy rápida |
| base   | ~145 MB | ~1 GB | Media-baja | Rápida |
| small  | ~466 MB | ~2 GB | **Media** | **Balanceada** ⭐ |
| medium | ~1.5 GB | ~5 GB | Alta | Lenta |
| large  | ~3 GB | ~10 GB | Muy alta | Muy lenta |

**Recomendación**: Usar `small` para balancear calidad y rendimiento.

---

### CORS

```env
# Origenes permitidos separados por coma (opcional)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://app.example.com
```

Si no se especifica, se usan los valores hardcodeados en `main.py`.

---

### Email (SMTP)

Para funcionalidades de reset password y notificaciones:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-password-de-aplicacion
SMTP_FROM=noreply@tutoria.com
```

**Nota Gmail**: Usa una "Contraseña de aplicación", NO tu contraseña normal.

[Cómo crear password de aplicación en Gmail](https://support.google.com/accounts/answer/185833)

---

### Archivos y Almacenamiento

```env
# Directorio base para uploads (default: ./uploads)
UPLOAD_DIR=./uploads

# Tamaño máximo de archivo en MB (default: 10)
MAX_FILE_SIZE_MB=10
```

---

### Logging

```env
# Nivel de logging (default: INFO)
# Opciones: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Directorio de logs (default: ./logs)
LOG_DIR=./logs
```

---

## 🔐 Generar SECRET_KEY Segura

### Método 1: Python (Recomendado)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Output**:
```
Dqvh1UKpy0oWxfTTWuIbl6waTyEcvvNco0XARguGBDw
```

### Método 2: OpenSSL

```bash
openssl rand -base64 32
```

### Método 3: Script Python Interactivo

```python
import secrets

# Generar clave segura
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")

# Guardar directamente en .env
with open(".env", "a") as f:
    f.write(f"\nSECRET_KEY={secret_key}\n")
```

### Método 4: Online (Solo para desarrollo)

⚠️ **NO usar en producción**:
- [Random.org](https://www.random.org/strings/)
- [LastPass Password Generator](https://www.lastpass.com/features/password-generator)

---

## 🌍 Configuración por Entorno

### Desarrollo Local

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tutoria_dev
SECRET_KEY=clave-de-desarrollo-cambiar-en-produccion
ENVIRONMENT=development
LOG_LEVEL=DEBUG
WHISPER_MODEL=small
```

### Testing

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tutoria_test
SECRET_KEY=clave-de-testing-diferente-a-produccion
ENVIRONMENT=testing
LOG_LEVEL=DEBUG
WHISPER_MODEL=tiny  # Más rápido para tests
```

### Staging

```env
DATABASE_URL=postgresql://user:pass@staging-db.example.com:5432/tutoria_staging
SECRET_KEY=clave-unica-de-staging
ENVIRONMENT=staging
LOG_LEVEL=INFO
WHISPER_MODEL=small
```

### Producción

```env
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/tutoria_prod
SECRET_KEY=clave-super-segura-de-produccion-muy-larga
ENVIRONMENT=production
LOG_LEVEL=WARNING
WHISPER_MODEL=medium  # Mejor precisión si hay recursos
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Más corto por seguridad
```

**Producción - Mejores Prácticas**:

1. ✅ Usa un gestor de secretos (AWS Secrets Manager, Vault, etc.)
2. ✅ Rota SECRET_KEY periódicamente
3. ✅ Usa variables de entorno del sistema, NO archivo .env
4. ✅ Habilita SSL en la conexión de BD
5. ✅ Configura CORS restrictivo
6. ✅ Reduce ACCESS_TOKEN_EXPIRE_MINUTES

---

## 🐛 Troubleshooting

### Error: "Field required" al iniciar

```
ValidationError: 1 validation error for Settings
SECRET_KEY
  Field required [type=missing, input_value={...}, input_type=dict]
```

**Solución**: Falta el archivo `.env` o la variable `SECRET_KEY`

```bash
# Verificar que existe .env
ls -la .env

# Si no existe, copiar desde ejemplo
cp .env.example .env

# Editar y agregar SECRET_KEY
nano .env
```

---

### Error: "Could not connect to database"

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Soluciones**:

1. Verificar que PostgreSQL está corriendo:
   ```bash
   sudo service postgresql status
   ```

2. Verificar credenciales en `DATABASE_URL`:
   ```bash
   psql -U postgres -d tutoria  # Probar conexión manual
   ```

3. Verificar que la base de datos existe:
   ```sql
   CREATE DATABASE tutoria;
   ```

---

### Error: "Invalid SECRET_KEY"

Si los tokens JWT no se validan:

1. Verifica que SECRET_KEY no tiene espacios al inicio/fin
2. Asegúrate de no haber cambiado SECRET_KEY después de generar tokens
3. Regenera tokens después de cambiar SECRET_KEY

---

### Verificar Configuración Actual

```python
# Script para verificar configuración
from app.settings import settings

print("✅ Configuración cargada:")
print(f"  DATABASE_URL: {settings.DATABASE_URL[:30]}...")  # Solo primeros caracteres
print(f"  SECRET_KEY: {'*' * 20} (oculta)")
print(f"  ALGORITHM: {settings.ALGORITHM}")
print(f"  TOKEN_EXPIRE: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} min")
print(f"  WHISPER_MODEL: {settings.WHISPER_MODEL}")
print(f"  ENVIRONMENT: {settings.ENVIRONMENT}")
```

---

## 📚 Referencias

- [Pydantic Settings Docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [12 Factor App - Config](https://12factor.net/config)
- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

## 🔒 Seguridad - Checklist

Antes de ir a producción:

- [ ] SECRET_KEY es única y generada aleatoriamente
- [ ] SECRET_KEY NO está en el código fuente
- [ ] .env está en .gitignore
- [ ] .env NO está en el repositorio
- [ ] DATABASE_URL usa credenciales seguras
- [ ] DATABASE_URL usa SSL en producción
- [ ] CORS está configurado restrictivamente
- [ ] ACCESS_TOKEN_EXPIRE_MINUTES es razonable (15-30 min)
- [ ] Variables sensibles están en gestor de secretos
- [ ] Logs NO exponen información sensible

---

**Creado**: 2025-12-27
**Versión**: 1.0.0
**Sistema**: TutorIA - Backend
