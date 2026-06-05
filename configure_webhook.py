import requests
import json

url = "http://evo-tb00z1qxnx0kt2oszk8hb0ek.187.127.15.180.sslip.io/webhook/set/Fluece%20Kids"
headers = {
    "apikey": "RK6LRQ3PJat6eQ2mOm9ZR8W7Y8Dy1gjS",
    "Content-Type": "application/json"
}

payload = {
    "webhook": {
        "enabled": True,
        "url": "http://yz66o5ldahh61lr8yye3zkph.187.127.15.180.sslip.io/webhook/whatsapp",
        "webhookByEvents": False,
        "webhookBase64": True,
        "events": [
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE",
            "QRCODE_UPDATED",
            "CONNECTION_UPDATE"
        ],
        "headers": {
            "Authorization": "Bearer Whook_Secret_4455667788"
        }
    }
}

try:
    print("Enviando requisição para configurar o webhook...")
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Resposta do servidor:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Erro ao configurar o webhook: {e}")
