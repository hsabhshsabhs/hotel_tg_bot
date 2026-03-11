import requests

# Токен вашего бота
BOT_TOKEN = "8138965801:AAGD5pEYg9AbflVqtkqjmEpOrFQS8zNS76U"

# Удаляем вебхук
url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
response = requests.get(url)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Проверяем информацию о вебхуке
info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
info_response = requests.get(info_url)

print(f"\nWebhook info: {info_response.json()}")
