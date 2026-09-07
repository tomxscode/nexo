# Nexo

Gestión de negocio SaaS multi-tenant para PYMEs: clientes, productos, cotizaciones con firma en línea, pedidos con pagos parciales y entregas, dashboard, notificaciones y modo oscuro.

Desarrollado en **Django 5.2** + **MySQL** + **Tailwind CSS** (Material 3), con UI en español y HTMX para interacciones parciales.

---

## Características

### Clientes y productos
- CRUD de clientes (RUT, contacto, notas) y productos o servicios (precio neto/bruto, margen %, stock, IVA).
- Productos inactivos se ocultan en nuevas cotizaciones.

### Cotizaciones con firma en línea
- Creación con ítems, descuentos por ítem y global, impuestos y folio `COT-*`.
- Página **pública** para el cliente: ver, **aprobar o rechazar** (firma con nombre/email/comentario) y descargar **PDF**.
- Flujo por estados: borrador → enviada → vista → aprobada/rechazada → convertida.
- Conversión a **pedido** con los ítems y el total de la cotización.
- Filtro "por vencer (15 días)" para cotizaciones enviadas o vistas próximas a expirar.

### Pedidos: pagos y entregas
- Pagos por **abono en %** (25 / 50 / monto libre) o **pago total**; estados al día / parcial / pagado.
- **Plantillas de etapas** de entrega (crear por líneas, eliminar) y aplicación por clic.
- Plantilla por defecto "Envío a domicilio" sembrada por migración.
- **Entrega automática** al completar el 100 % de las etapas (`delivered_at`).
- **Etapas fijas tras la entrega**: la UI y el backend bloquean nuevas etapas/plantillas/reaperturas.
- Feedback de pagos y acciones vía mensajes codificados por severidad.

### Dashboard
- KPIs del período (ventas, cobrado, deuda, cotizaciones, pedidos) con **Δ% vs período anterior**.
- Selector de período: este mes, mes pasado, últimos 30 días, 3 meses, año, todo.
- Alertas de pendientes: cotizaciones por vencer, por cobrar y entregas en curso.
- Panorama por estado de cotización, estado financiero y listados recientes.
- Reutiliza HTMX para navegar entre períodos sin recargar la página.

### Notificaciones in-app (campana)
- Avisos al equipo (propietario/administrador/ventas) cuando una cotización es **vista, aprobada o rechazada**.
- **Sweep por vencimiento** (a petición, sin cron) con umbrales de **15, 10, 5 y 1 día**, idempotente.
- Marcar una o todas como leídas; panel colaborativo en el topbar.

### Configuración y perfil
- **Negocio**: nombre, RUT, contacto, dirección, giro, plazos, garantía, logo, IVA por defecto y **moneda (CLP/USD/UF)**.
- **Miembros**: alta por correo (con contraseña temporal), cambio de rol (propietario/administrador/ventas/solo lectura) y remoción; solo propietarios/administradores gestionan.
- **Perfil**: datos personales, cambio de contraseña, **cambio de negocio activo** (multi-negocio) y tema.

### Modo oscuro
- Paletas Material 3 definidas como variables CSS (`:root` para claro, `.dark` para oscuro).
- Toggle en el topbar que persiste la preferencia por usuario (`system` / light / dark) y se aplica sin parpadeo.

### Multi-tenant y roles
- Arrendamiento por negocio (`Tenant`) con folios únicos por tenant.
- Roles: propietario, administrador, ventas y solo lectura.

---

## Stack técnico

| Capa | Tecnología |
| --- | --- |
| Backend | Django 5.2 (Python 3.12+) |
| Base de datos | MySQL 8 (vía PyMySQL) |
| Frontend | Tailwind CSS 3 (Material 3), HTMX 2 |
| PDF | xhtml2pdf |
| Tipografías/iconos | Plus Jakarta Sans, Material Symbols |

---

## Estructura del proyecto

```
nexo/
├── apps/                  # Aplicaciones de negocio
│   ├── core/              # Tenant, User (tema), membresías, utilidades
│   ├── account/           # Login, signup, onboarding, perfil, tema
│   ├── dashboard/         # KPIs, período, alertas
│   ├── clients/           # CRUD de clientes
│   ├── products/          # Productos, servicios, categorías
│   ├── quotations/        # Cotizaciones, firma pública, PDF, conversión
│   ├── orders/            # Pedidos, pagos por %, plantillas, entregas
│   ├── settings/          # Configuración de negocio y miembros
│   └── notifications/     # Campana, sweep de vencimientos
├── templates/             # Plantillas (workspace + páginas públicas)
├── theme/                 # Tailwind: input.css + tailwind.config.js
├── static/                # Estáticos (nexo.css se compila desde theme/)
├── nexo/                  # settings, urls, wsgi/asgi
└── manage.py
```

---

## Puesta en marcha

### Requisitos
- Python 3.12+
- MySQL 8 (local o Docker)
- Node.js 20+ (solo para compilar el CSS de Tailwind)

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/tomxscode/nexo.git
cd nexo

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Crear la base de datos

```sql
CREATE DATABASE nexo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nexo'@'localhost' IDENTIFIED BY 'nexo_dev_pw';
GRANT ALL PRIVILEGES ON nexo.* TO 'nexo'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configurar variables de entorno

Copia `.env` (opcional en desarrollo; usa los defaults de `nexo/settings.py`):

```bash
export NEXO_DB_NAME=nexo
export NEXO_DB_USER=nexo
export NEXO_DB_PASSWORD=nexo_dev_pw
export NEXO_DB_HOST=127.0.0.1
export NEXO_DB_PORT=3306
export NEXO_SECRET_KEY=genera-una-aleatoria
```

> En desarrollo `NEXO_DEBUG=1` (default). En producción pon `NEXO_DEBUG=0` y define `NEXO_ALLOWED_HOSTS`.

### 4. Migrar y crear tu cuenta

```bash
python manage.py migrate
python manage.py runserver
```

Abre **http://localhost:8000/** y usa **Crear cuenta gratis** (signup) para crear el propietario del primer negocio, o crea un superusuario con `python manage.py createsuperuser` para el admin de Django (`/admin/`).

### 5. Compilar el CSS (Tailwind)

`static/css/nexo.css` no se versiona (ver `.gitignore`); en un clon nuevo compílalo:

```bash
cd theme
npm install
npm run build        # genera ../static/css/nexo.css (minificado)
```

En desarrollo puedes usar `npm run dev` (watch) mientras editas templates.

---

## Variables de entorno

| Variable | Default | Descripción |
| --- | --- | --- |
| `NEXO_SECRET_KEY` | clave de desarrollo | Secret key de Django (cámbiala en producción) |
| `NEXO_DEBUG` | `1` | Modo depuración activado/desactivado |
| `NEXO_ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver` | Hosts permitidos (lista separada por comas) |
| `NEXO_DB_NAME` | `nexo` | Nombre de la base de datos |
| `NEXO_DB_USER` | `nexo` | Usuario MySQL |
| `NEXO_DB_PASSWORD` | `nexo_dev_pw` | Contraseña MySQL |
| `NEXO_DB_HOST` | `127.0.0.1` | Host MySQL |
| `NEXO_DB_PORT` | `3306` | Puerto MySQL |

---

## Producción

```bash
# 1. Compilar estilos y recolectar estáticos
cd theme && npm run build && cd ..
python manage.py collectstatic --noinput

# 2. Variables de entorno
export NEXO_DEBUG=0
export NEXO_ALLOWED_HOSTS=midominio.cl
export NEXO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# 3. Servir con Gunicorn + Nginx (los estáticos y /media/ los sirve Nginx)
gunicorn nexo.wsgi:application
```

---

## Notas

- Los **folios** de clientes, cotizaciones (`COT-*`) y pedidos son únicos por negocio.
- Las **plantillas de etapas** se siembran por migración ("Envío a domicilio") y se pueden crear/eliminar desde Pedidos → Plantillas.
- Las **notificaciones de vencimiento** se generan bajo demanda en cada request (no requieren cron); los umbrales son 15, 10, 5 y 1 día.