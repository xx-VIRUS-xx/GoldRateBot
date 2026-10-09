from fastapi import APIRouter, FastAPI, Request,Response
from app.services.whatsapp_service import send_template_message
from app.database import save_user_activity
import os

import json
router=APIRouter()

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "goldrate123")
print("🔥🔥 WHATSAPP ROUTER LOADED 🔥🔥")

# @router.post("/{path:path}")
# async def catch_all(path: str, request: Request):
#     print("🔥 CATCH-ALL HIT:", path)
#     return {"ok": True}

@router.post("/")
async def root_post():
    return {"status": "ok"}

@router.get("/")
async def root_verify(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(content="OK")
@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("MODE:", mode)
    print("TOKEN:", token)
    print("CHALLENGE:", challenge)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Verification failed", status_code=403)

# @router.get("/debug-send")
# async def debug_send():
#     send_template_message(
#         "<TEST_PHONE_NUMBER>",
#         "DEBUG DIRECT SEND TEST"
#     )
#     return {"ok": True}

# @router.post("/webhook")
# async def webhook(request: Request):
#     # body = await request.body()
#     print("🔥 WEBHOOK HIT")
#     # print(body.decode())

#     send_template_message(
#         "<TEST_PHONE_NUMBER>",  # YOUR test number hardcoded
#         "Webhook is working ✅"
#     )

#     return {"status": "ok"}
@router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    # print("WEBHOOK BODY:", body)
    if not body:
        return {"status": "empty"}

    data = json.loads(body)

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            messages = value.get("messages")
            if not messages:
                continue  # status updates, delivery receipts, etc.

            contacts = value.get("contacts", [])
            name = (
                contacts[0]
                .get("profile", {})
                .get("name", "Customer")
                if contacts else "Customer"
            )

            for msg in messages:
                phone = msg.get("from")
                text = msg.get("text", {}).get("body", "").strip().lower()

                print("📩 INCOMING:", phone, text)

                save_user_activity(phone)
                tosend=f'''Welcome {name} ✨\n\nYou will now receive daily Gold & Silver rates on WhatsApp.\nReply "HI" anytime to continue updates.'''
                if text == "hi":
                    send_template_message(
                        phone,
                        tosend
                    )

    return {"status": "ok"}

