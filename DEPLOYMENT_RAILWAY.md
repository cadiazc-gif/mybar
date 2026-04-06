# Deploy en Railway con PostgreSQL y acceso de administrador

## 1) Variables de entorno mínimas
En el servicio web de Railway, configura estas variables:

- `DJANGO_SECRET_KEY`: cadena larga y única.
- `DJANGO_DEBUG`: `False` en producción.
- `DJANGO_ALLOWED_HOSTS`: hosts separados por coma (ej: `mybar-production.up.railway.app`).
- `DJANGO_CSRF_TRUSTED_ORIGINS`: orígenes completos con `https://` separados por coma.
- `DATABASE_URL`: URL de PostgreSQL (Railway la inyecta al conectar un plugin de Postgres).

Variables para crear/actualizar el admin al arrancar:

- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

## 2) Flujo de arranque esperado
`start.sh` ejecuta automáticamente:

1. `python manage.py migrate`
2. Bootstrap del superusuario usando variables `DJANGO_SUPERUSER_*`
3. `gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080}`

## 3) Checklist de troubleshooting (admin no puede entrar)
1. Verifica que `DATABASE_URL` exista en Railway.
2. Confirma que la app quedó enlazada al mismo Postgres donde corre `migrate`.
3. Re-deploy tras cambiar variables.
4. Revisa logs del deploy y busca:
   - `Admin ready: <usuario> | created=True/False`
5. Si olvidaste contraseña, cambia `DJANGO_SUPERUSER_PASSWORD` y vuelve a desplegar.

## 4) Endpoints útiles
- Admin: `/admin/`
- Diagnóstico restringido a staff: `/runtime-diagnose-2026/`

## 5) Recomendaciones de seguridad
- Nunca usar `DEBUG=True` en producción.
- Rotar `DJANGO_SECRET_KEY` si estuvo expuesta.
- No publicar endpoints de diagnóstico sin autenticación de staff.
