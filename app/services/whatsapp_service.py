import os
import requests

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

print("🚨 TOKEN:", os.getenv("WHATSAPP_TOKEN"))
print("🚨 PHONE_NUMBER_ID:", os.getenv("PHONE_NUMBER_ID"))

print("🔥🔥 WHATSAPP SERVICE LOADED 🔥🔥")
def send_template_message(to, message):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "recipient_type": "individual",
        "type": "text",
        "text": {
            "body": message
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    # return response.json()
    # print(response.status_code, response.text)