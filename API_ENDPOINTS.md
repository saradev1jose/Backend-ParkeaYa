# API Endpoints - PanelGeneral (para cliente móvil)

Este documento recoge los endpoints REST disponibles en el proyecto (prefijo por defecto: `/api/`).
Incluye métodos HTTP, permisos aproximados y notas útiles para consumo desde una app móvil.

-- Autenticación / Tokens
- `POST /api/token/` — Obtener access + refresh token (SimpleJWT). Body: `username`, `password`.
- `POST /api/token/refresh/` — Refrescar token. Body: `refresh`.
- `POST /api/login/` — (legacy) alias para obtención de token.
- `POST /api/users/auth/login/` — `MyTokenObtainPairView` (login desde users app).

-- Users (prefijo `/api/users/`)
- `POST /api/users/auth/register/client/` — Registrar cliente.
- `POST /api/users/auth/register/owner/` — Registrar owner.
- `POST /api/users/panel/login/` — Login especial para panel web.
- `GET  /api/users/profile/` — Obtener perfil del usuario autenticado.
- `POST  /api/users/profile/change-password/` — Cambiar contraseña (autenticado).
- `POST /api/users/panel/check-access/` — Verificar acceso al panel.
- Dashboard stats:
  - `GET /api/users/admin/dashboard/stats/` (admin)
  - `GET /api/users/owner/dashboard/stats/` (owner)
  - `GET /api/users/client/dashboard/stats/` (client)
- Routers (ModelViewSets) registrados dentro de `users.urls` (CRUD):
  - `/api/users/admin/users/` — `AdminUserViewSet` (admin CRUD)
  - `/api/users/owner/profile/` — `OwnerUserViewSet` (owner profile endpoints + `me` action)
  - `/api/users/client/profile/` — `ClientUserViewSet`
  - `/api/users/cars/` — `CarViewSet` (vehículos)
  - `GET/PUT /api/users/owner/me/` — endpoint `owner/me` para obtener/actualizar perfil del owner.

-- Parking (prefijo `/api/parking/`)
- Dashboard / data:
  - `GET /api/parking/dashboard/`
  - `GET /api/parking/dashboard/admin/` (admin)
  - `GET /api/parking/dashboard/owner/` (owner)
  - `GET /api/parking/dashboard/owner/complete/` (owner full)
  - `GET /api/parking/dashboard/stats/`
  - `GET /api/parking/dashboard/recent-reservations/`
- Approval (solicitudes):
  - `GET/POST   /api/parking/approval/requests/` — `ParkingApprovalViewSet` (listar, crear)
  - `GET        /api/parking/approval/requests/{id}/` — detalle
  - `POST       /api/parking/approval/requests/{id}/aprobar/` — aprobar (admin)
  - `POST       /api/parking/approval/requests/{id}/rechazar/` — rechazar (admin)
  - `GET        /api/parking/approval/requests/pendientes/` — solicitudes pendientes (admin)
  - `GET        /api/parking/approval/requests/estadisticas/` — stats (admin)
  - `GET        /api/parking/approval/requests/mis_solicitudes/` — solicitudes del owner autenticado
- Parkings (router `parkings`):
  - `GET/POST   /api/parking/parkings/` — listar / crear (crear por owner crea solicitud de aprobación)
  - `GET/PUT/PATCH/DELETE /api/parking/parkings/{id}/` — detalle / edición / borrado
  - `GET        /api/parking/parkings/mapa/` — listado sin paginar para mapa (action `mapa`)
  - `GET        /api/parking/my-parkings/` — parkings del owner autenticado
  - `POST       /api/parking/parkings/{id}/toggle_activation/` — activar/desactivar
  - `POST       /api/parking/parkings/{id}/approve/` — aprobar (admin)
  - `POST       /api/parking/parkings/{id}/reject/` — rechazar (admin)
  - `GET        /api/parking/admin/pending-parkings/` — listado parkings pendientes (admin)
  - `GET        /api/parking/admin/approved-parkings/` — listado parkings aprobados (admin)

Nota: además del prefijo `/api/parking/` el proyecto registra el mismo `ParkingLotViewSet` en el router principal (`/api/parkings/`), por lo que ambas rutas pueden existir simultáneamente: `/api/parkings/` y `/api/parking/parkings/`.

-- Reservations (prefijo `/api/reservations/`)
- Router `reservations` (CRUD): `/api/reservations/reservations/` (list, create, retrieve...)
- Operaciones y acciones:
  - `POST   /api/reservations/{codigo_reserva}/checkin/` — check-in por código
  - `POST   /api/reservations/{codigo_reserva}/checkout/` — check-out
  - `POST   /api/reservations/{codigo_reserva}/cancel/` — cancelar reserva
  - `POST   /api/reservations/{codigo_reserva}/extend/` — extender reserva
  - `GET    /api/reservations/tipos/` — tipos de reserva disponibles
  - `GET    /api/reservations/client/active/` — reservas activas del cliente
  - `GET    /api/reservations/client/mis-reservas/` — mis reservas (cliente)
  - `GET    /api/reservations/owner/reservas/` — reservas para dueño (owner)
  - `GET    /api/reservations/owner/parking/{parking_id}/` — reservas por estacionamiento (owner)
  - `GET    /api/reservations/stats/` — estadísticas generales
  - `GET    /api/reservations/dashboard/admin/stats/` — admin stats
  - `GET    /api/reservations/dashboard/owner/stats/` — owner stats

-- Payments (prefijo `/api/payments/`)
- Router principal: `/api/payments/` (list, create, retrieve...)
- Acciones específicas:
  - `POST /api/payments/{id}/process/` — procesar pago pendiente
  - `POST /api/payments/{id}/refund/` — solicitar reembolso
  - `GET  /api/payments/pending/` — pagos pendientes del usuario
  - `GET  /api/payments/transactions/stats/` — (admin) estadísticas
  - `GET  /api/payments/transactions/` — (admin) transacciones
  - `GET  /api/payments/?parking_id=..` — (owner/admin) filtrado por parking (nota: el viewset también soporta `by_parking`)

-- Tickets (prefijo `/api/tickets/`)
- Router: `/api/tickets/tickets/` (CRUD)
- Validación / extras:
  - `POST /api/tickets/tickets/{id}/validate_ticket/` — validar ticket (owner/admin)
  - `POST /api/tickets/tickets/{id}/cancel/` — cancelar ticket
  - `GET  /api/tickets/tickets/validos/` — tickets válidos del usuario
  - `GET  /api/tickets/tickets/by_parking/?parking_id=..` — tickets por parking
  - `POST /api/tickets/validate/` — `TicketValidationAPIView` (público para validación vía QR)
  - `GET /api/tickets/parking/{parking_id}/` — tickets por parking (ruta añadida en `parkeaya/urls.py`)

-- Notifications (prefijo `/api/notifications/`)
- Router: `/api/notifications/notifications/` (list, create, retrieve, destroy)
- Variantes: `/api/notifications/admin/notifications/`, `/api/notifications/owner/notifications/` (viewsets con filtros por rol)
- Acciones destacadas (definidas en `NotificationViewSet`):
  - `GET  /api/notifications/notifications/unread_count/` — contar no leídas
  - `POST /api/notifications/notifications/{id}/mark_read/` — marcar como leída
  - `POST /api/notifications/notifications/mark_all_read/` — marcar todas
  - `POST /api/notifications/notifications/mark_multiple_read/` — marcar varias (body: `notification_ids`)
  - `POST /api/notifications/notifications/create_notification/` — crear notificación (solo admin)
  - `GET  /api/notifications/notifications/?type=...&unread=true` — query params para filtrar

-- Analytic (prefijo `/api/analytics/`)
- `GET /api/analytics/admin/dashboard/`
- `GET /api/analytics/admin/revenue/`
- `GET /api/analytics/admin/users/`
- `GET /api/analytics/owner/dashboard/`
- `GET /api/analytics/owner/revenue/`
- `GET /api/analytics/owner/performance/` (y `/owner/performance/{parking_id}/`)
- `GET /api/analytics/owner/reservations/`

-- Complaints (prefijo `/api/complaints/`)
- Router: `/api/complaints/complaints/` (CRUD para denuncias/quejas)

-- Endpoints Legacy / Extras
- `auth/` — incluye `dj_rest_auth` endpoints (login, logout, password reset, etc.)
- `GET /api/dashboard/stats/` and `GET /api/dashboard/recent-reservations/` — mapeados a funciones en `parking` y `reservations` (legacy)

-- Autorización (resumen)
- Muchas rutas requieren JWT Bearer (`Authorization: Bearer <access_token>`). Usar `/api/token/` para obtener token.
- Rutas marcadas `admin`/`owner` requieren roles específicos (se usan permisos personalizados en el backend).

-- Ejemplos rápidos (curl)

1) Obtener token (login):

```bash
curl -X POST https://mi-api.example.com/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "usuario", "password": "clave"}'
```

Respuesta esperada: `{"access": "...", "refresh": "..."}`

2) Listar notificaciones (usar token obtenido):

```bash
curl -X GET https://mi-api.example.com/api/notifications/notifications/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

3) Marcar una notificación como leída:

```bash
curl -X POST https://mi-api.example.com/api/notifications/notifications/123/mark_read/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

-- Notas finales
- El proyecto contiene duplicados de rutas (router principal y prefijos específicos de apps). Para la app móvil recomiendo usar los prefijos consistentes del tipo `/api/<app>/...` (ej. `/api/parking/parkings/`, `/api/notifications/notifications/`) o definir en el cliente una lista limpia con los endpoints que realmente usarás.
- Si quieres, puedo:
  - Generar un archivo JSON (OpenAPI / Postman collection) con los endpoints que utilices.
  - Limpiar/enumerar solo los endpoints que la app móvil necesita (autenticación, listar parkings, reservar, pagos, notificaciones, perfil).

---
+Fecha: 2025-11-18
