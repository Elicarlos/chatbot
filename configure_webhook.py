import requests
import json

url = "http://vrf819pc4m4s2o4w7uivmtmb.187.127.15.180.sslip.io/webhook/set/Fluence%20Kids"
headers = {
    "apikey": "2B025020A1F4-446B-9F6A-CA73B570DAAD",
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
