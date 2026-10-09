# GoldRateBot

An early prototype of a WhatsApp bot for a jewellery business: customers message the business number, get added to a subscriber list, and are meant to receive daily gold and silver rates. A FastAPI service handles Meta's WhatsApp Cloud API webhook, replies to "HI" with a welcome message, and records each user's last activity in SQLite.

> **Status: prototype.** Only the webhook handshake, the "HI" welcome reply and user-activity tracking work. Rate fetching, daily broadcasting, inventory, the scheduler and the admin page are empty placeholder files.

System design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Problem it addresses

Jewellers quote gold and silver rates that change daily, and customers keep asking for them. A WhatsApp subscription saves both sides the back-and-forth: customers opt in once, and the shop pushes the day's rates.

## What works today

| Piece | Where | State |
|---|---|---|
| Webhook verification (`GET /webhook`, `GET /`) | `app/routers/whatsapp.py` | Working, covered by tests |
| Incoming message handling (`POST /webhook`) | `app/routers/whatsapp.py` | Working: ignores status updates, replies "Welcome ..." when the text is `hi`, records the sender |
| Sending a message through the Graph API | `app/services/whatsapp_service.py` | Working for plain text messages |
| User activity store (`users(phone, last_seen)`) | `app/database.py` | Working (SQLite) |
| Rates, inventory, store and user models; scheduler; message builder; admin page | `app/models/`, `app/routers/rate.py`, `app/routers/inventory.py`, `app/services/scheduler.py`, `app/services/message_builder.py`, `app/templates/admin.html` | Empty placeholders |
| `test_webhook_app.py` | repo root | An earlier standalone prototype of the webhook (not a test file) |

## Setup and run

Python 3.12 (the dependencies were pinned from the project's environment).

```bash
pip install -r requirements.txt
cp .env.example .env         # fill in WHATSAPP_TOKEN, PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN
uvicorn app.main:app --reload
```

Meta's webhook configuration needs a public HTTPS URL pointing at `/webhook` and the same verify token you put in `.env`. If `WHATSAPP_VERIFY_TOKEN` is unset the app falls back to its old built-in value, so set your own. Run from the project root: the SQLite file `db.sqlite3` is created in the current directory.

## Tests

```bash
pip install pytest httpx
python3 -m pytest tests -q
```

Six tests cover the handshake (accepted, rejected, token from the environment), the "HI" reply and user recording, plain messages, and ignored empty or status-only payloads. They run against a temporary database and never call the WhatsApp API.

## Limitations and next steps

- The product is not built yet: no source of gold or silver rates, no daily send, no unsubscribe, no admin view.
- Messages are sent as plain `text`. WhatsApp generally only allows free-form text within a customer-initiated conversation window; business-initiated daily broadcasts normally need an approved message template, so the planned daily push needs redesigning around templates. Check Meta's current rules.
- Incoming webhook `POST`s are not authenticated: `X-Hub-Signature-256` is not checked.
- Send results are not checked and the HTTP call has no timeout or retry.
- Incoming phone numbers and message text are printed to stdout.
- `datetime.utcnow()` is deprecated, and the database path is relative to the working directory.
- The webhook verify token has a built-in fallback value; replace it, and rotate any WhatsApp access token that has ever been logged or shared.
- No LICENSE has been chosen.
