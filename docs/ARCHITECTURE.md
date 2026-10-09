# Architecture

A single FastAPI service that sits between Meta's WhatsApp Cloud API and a small SQLite database.

## System context

```
 Customer's WhatsApp
        |  message
        v
 Meta WhatsApp Cloud API  --- webhook (HTTPS) --->  FastAPI service
                                                     |
                      GET /webhook  verify handshake |  POST /webhook  incoming messages
                                                     v
                                          app/routers/whatsapp.py
                                           |                  |
                         save_user_activity|                  | send_template_message
                                           v                  v
                                   app/database.py     app/services/whatsapp_service.py
                                   SQLite users        POST graph.facebook.com/v22.0/<id>/messages
                                   (phone, last_seen)          |
                                                               v
                                                      Customer's WhatsApp
```

## Components

| Module | Responsibility |
|---|---|
| `app/main.py` | Creates the FastAPI app, loads `.env`, mounts the WhatsApp router (rate and inventory routers are commented out) |
| `app/routers/whatsapp.py` | Webhook verification, message parsing, the welcome reply, activity recording |
| `app/services/whatsapp_service.py` | Builds and sends a text message through the Graph API using the access token and phone number id |
| `app/database.py` | One shared SQLite connection in autocommit mode behind a lock; creates the `users` table on import; `save_user_activity` upserts the phone number with a UTC timestamp |
| `app/models/`, `app/routers/rate.py`, `app/routers/inventory.py`, `app/services/scheduler.py`, `app/services/message_builder.py`, `app/templates/admin.html` | Planned modules for rates, inventory, daily sending and an admin page; currently empty |

## Request flow

**Verification.** Meta calls `GET /webhook` with `hub.mode=subscribe`, `hub.verify_token` and `hub.challenge`. If the token matches `WHATSAPP_VERIFY_TOKEN`, the challenge is echoed back as plain text; otherwise the response is 403.

**Incoming message.** `POST /webhook` receives Meta's payload. The handler walks `entry -> changes -> value`, skips events without `messages` (delivery receipts and status updates), reads the sender's number, profile name and lowercase text, records the user, and if the text is `hi` sends a welcome message through the Graph API. The endpoint always answers `{"status": "ok"}` quickly so Meta does not retry.

## Key design decisions

- **Secrets from the environment.** The access token, phone number id and verify token come from `.env` (git-ignored), with `.env.example` documenting them.
- **Ignore what is not a message.** Status callbacks arrive on the same endpoint, so the handler filters on the presence of `messages` rather than assuming every call is a user message.
- **Tiny persistence.** The only state is who messaged and when. `INSERT OR REPLACE` keyed on the phone number keeps one row per user, which is enough to know who can be messaged.
- **Thin sending layer.** Sending is isolated in one function so the rest of the code (and tests) can replace it.

## Known limitations

- Webhook payloads are not signature-verified.
- A single shared SQLite connection with a lock is fine for a prototype but will not scale across workers.
- Free-form text messages cannot be used for business-initiated daily broadcasts under WhatsApp's usual rules; a template-based design is needed for the planned feature.
- Send failures are silent: no status check, timeout or retry.
- The daily-rate pipeline (source of rates, scheduling, formatting) does not exist yet.
