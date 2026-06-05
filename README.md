# House Price Prediction API

API REST construida con FastAPI para predicción de precios de casas, con persistencia de datos en base de datos relacional y despliegue en Railway.

---

## Descripción

La API expone endpoints para:
- Validar la conexión a la base de datos (`/health`)
- Generar predicciones de precio de casas a partir de un archivo CSV (`/predict`)
- Persistir tanto los datos de entrada como los resultados de predicción en la base de datos

El modelo utilizado es una regresión lineal (`linear_regression.joblib`) entrenado con features seleccionadas del dataset Ames Housing.

---

## Estructura del proyecto

```
mlops-demo/
├── main.py                    # Aplicación FastAPI principal
├── linear_regression.joblib   # Modelo preentrenado
├── selected_features.csv      # Lista de features requeridas
├── requirements.txt           # Dependencias
├── railway.toml               # Configuración de despliegue en Railway
├── .env.example               # Plantilla de variables de entorno
└── README.md
```

---

## Endpoints

### `GET /`
Retorna un mensaje de bienvenida.

```json
{"message": "House Price Prediction API", "version": "1.0.0"}
```

### `GET /health`
Verifica la conexión a la base de datos.

**Respuesta exitosa:**
```json
{"status": "success", "message": "Connected to the database successfully."}
```

**Respuesta con error:**
```json
{"status": "error", "message": "<detalle del error>"}
```

### `POST /predict`
Recibe un archivo CSV con los datos de entrada, genera predicciones y las persiste.

- **Body:** `multipart/form-data` con campo `file` (archivo CSV con las features del modelo)
- **Respuesta:**
```json
{
  "file_name": "test_data.csv",
  "count": 3,
  "predictions": [180000.5, 225000.0, 310500.75]
}
```

Los datos de entrada se guardan en la tabla `inputs` y los resultados en la tabla `predictions`.

---

## Base de datos

Las tablas se crean automáticamente al iniciar la aplicación:

```sql
-- Tabla de inputs (datos de entrada procesados)
CREATE TABLE inputs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name    VARCHAR(255),
    feature_data TEXT,        -- JSON con los valores de cada feature
    created_at   DATETIME
);

-- Tabla de predicciones (resultados del modelo)
CREATE TABLE predictions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name    VARCHAR(255),
    prediction   FLOAT,
    created_at   DATETIME
);
```

---

## Ejecución local con venv

### 1. Crear y activar el entorno virtual

```bash
# Crear el venv dentro del proyecto
python -m venv venv

# Activar en Linux/macOS
source venv/bin/activate

# Activar en Windows (PowerShell)
# venv\Scripts\Activate.ps1
```

> Sabrás que está activo porque el prompt cambiará a `(venv) $`.

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

El archivo `.env` generado usa **SQLite** por defecto, no necesitas ninguna configuración
adicional para probar en local. Si quieres apuntar a un MySQL externo, edita la línea:

```
SQLALCHEMY_DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DB_NAME
```

### 4. Levantar el servidor

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- API disponible en: `http://localhost:8000`
- Documentación interactiva (Swagger UI): `http://localhost:8000/docs`
- Documentación alternativa (ReDoc): `http://localhost:8000/redoc`

### 5. Probar los endpoints localmente

```bash
# Verificar salud / conexión DB
curl http://localhost:8000/health

# Enviar CSV para predicción
curl -X POST http://localhost:8000/predict \
  -F "file=@tu_archivo.csv"
```

### 6. Desactivar el venv cuando termines

```bash
deactivate
```

---

## Despliegue en Railway — Manual completo

### Requisitos previos

- Cuenta gratuita en [railway.app](https://railway.app) (puedes registrarte con GitHub)
- Repositorio del proyecto subido a GitHub

---

### Paso 1 — Crear cuenta en Railway

1. Ve a [https://railway.app](https://railway.app) y haz clic en **"Start a New Project"** o **"Login"**.
2. Selecciona **"Login with GitHub"** para vincular tu cuenta de GitHub directamente.
3. Autoriza el acceso de Railway a tu cuenta de GitHub cuando se solicite.

---

### Paso 2 — Subir el código a GitHub

Si aún no tienes el repo en GitHub:

```bash
# Dentro de la carpeta del proyecto
git init          # si aún no es un repo git
git add .
git commit -m "Initial commit"

# Crear repo en GitHub y luego:
git remote add origin https://github.com/TU_USUARIO/mlops-demo.git
git push -u origin main
```

> **Importante:** No subas el archivo `.env` (ya está en `.gitignore`).  
> Sí deben estar en el repo: `main.py`, `requirements.txt`, `railway.toml`,
> `selected_features.csv` y `linear_regression.joblib`.

---

### Paso 3 — Crear un nuevo proyecto en Railway

1. En el dashboard de Railway, haz clic en **"New Project"**.
2. Selecciona **"Deploy from GitHub repo"**.
3. Si es la primera vez, haz clic en **"Configure GitHub App"** y da acceso al repositorio `mlops-demo`.
4. Selecciona el repositorio de la lista y haz clic en **"Deploy Now"**.

Railway comenzará a construir la imagen automáticamente usando el archivo `railway.toml`.

---

### Paso 4 — Agregar la base de datos MySQL

1. Dentro de tu proyecto en Railway, haz clic en **"+ New"** (o **"Add a Service"**).
2. Selecciona **"Database"** → **"Add MySQL"**.
3. Railway provisiona una base de datos MySQL y la agrega al mismo proyecto.
4. Haz clic en el servicio MySQL recién creado para ver sus detalles.
5. Ve a la pestaña **"Variables"** del servicio MySQL. Verás variables como:
   - `MYSQLHOST`
   - `MYSQLPORT`
   - `MYSQLUSER`
   - `MYSQLPASSWORD`
   - `MYSQLDATABASE`
   - `MYSQL_URL` ← esta es la más útil, tiene el formato completo

---

### Paso 5 — Conectar la API con la base de datos

1. Haz clic en el servicio de tu **API** (el que viene del repo de GitHub).
2. Ve a la pestaña **"Variables"**.
3. Haz clic en **"New Variable"** y agrega:

   | Variable | Valor |
   |---|---|
   | `SQLALCHEMY_DATABASE_URL` | `mysql+pymysql://${{MySQL.MYSQLUSER}}:${{MySQL.MYSQLPASSWORD}}@${{MySQL.MYSQLHOST}}:${{MySQL.MYSQLPORT}}/${{MySQL.MYSQLDATABASE}}` |

   > Railway permite referenciar variables de otros servicios del mismo proyecto con la
   > sintaxis `${{NombreServicio.VARIABLE}}`. Esto evita copiar y pegar credenciales.

4. Haz clic en **"Add"** para guardar. Railway redesplegará la API automáticamente.

---

### Paso 6 — Verificar el despliegue

1. En el servicio de la API, ve a la pestaña **"Deployments"** y espera a que el estado
   cambie a ✅ **"Success"**.
2. Ve a la pestaña **"Settings"** → sección **"Networking"** → haz clic en
   **"Generate Domain"** para obtener una URL pública (ej. `https://mlops-demo-production.up.railway.app`).
3. Prueba los endpoints con esa URL:

```bash
# Health check (debe confirmar conexión a la DB)
curl https://TU-DOMINIO.up.railway.app/health

# Predicción
curl -X POST https://TU-DOMINIO.up.railway.app/predict \
  -F "file=@tu_archivo.csv"
```

---

### Paso 7 — Verificar los datos en la base de datos

1. En Railway, haz clic en el servicio **MySQL**.
2. Ve a la pestaña **"Data"** (o usa el cliente de Railway en el navegador).
3. Ejecuta las consultas:

```sql
SELECT * FROM inputs LIMIT 10;
SELECT * FROM predictions LIMIT 10;
```

Deberías ver los registros insertados por el endpoint `/predict`.

---

### Resumen de la arquitectura en Railway

```
GitHub repo
    │
    ▼
Railway Project
    ├── Servicio API  (FastAPI · uvicorn · puerto $PORT)
    │       └── Variable: SQLALCHEMY_DATABASE_URL → apunta al MySQL
    └── Servicio MySQL  (base de datos relacional)
            ├── tabla: inputs
            └── tabla: predictions
```

---

### Solución de problemas comunes

| Problema | Solución |
|---|---|
| Build falla con error de dependencias | Revisa que `requirements.txt` esté en la raíz del repo |
| `/health` retorna `503` | La variable `SQLALCHEMY_DATABASE_URL` no está configurada o es incorrecta |
| Error `Can't connect to MySQL` | Verifica que el servicio MySQL esté en el mismo proyecto de Railway |
| Puerto no disponible | Railway asigna el puerto via `$PORT`; el `railway.toml` ya lo configura correctamente |
| Modelo no encontrado | Asegúrate de que `linear_regression.joblib` está en el repo (no en `.gitignore`) |
