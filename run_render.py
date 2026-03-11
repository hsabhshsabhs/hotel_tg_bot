import threading
import os
import http.server
import socketserver
import bot
from logger import logger

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running and healthy!")
    
    def log_message(self, format, *args):
        # Подавляем логирование обычных GET запросов, чтобы не забивать консоль
        return

def run_health_check_server():
    port = int(os.getenv("PORT", 8080))
    with socketserver.TCPServer(("0.0.0.0", port), HealthCheckHandler) as httpd:
        logger.info(f"🚀 Health check server started on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Запускаем сервер проверки здоровья в фоновом потоке
    health_thread = threading.Thread(target=run_health_check_server, daemon=True)
    health_thread.start()
    
    # Запускаем основного бота (этот вызов блокирующий)
    try:
        logger.info("🤖 Starting Telegram Bot via run_render.py...")
        bot.main()
    except Exception as e:
        logger.error(f"❌ Critical error in bot execution: {e}")
        os._exit(1)
