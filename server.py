# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - Web 服务器
================================
提供日报和门户页面的 HTTP 访问
默认端口：18088
"""

import sys
import os
import io
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

# Windows GBK 兼容
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 18088


class IntelHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory or BASE_DIR, **kwargs)

    def end_headers(self):
        # CORS + 缓存控制
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):
        # 根路径 → 门户
        if self.path == "/" or self.path == "/index.html":
            self.path = "/portal/index.html"
        super().do_GET()

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    os.chdir(BASE_DIR)
    server = HTTPServer(("0.0.0.0", PORT), partial(IntelHandler, directory=BASE_DIR))
    print(f"🎮 游戏异业合作情报站 Web 服务器已启动")
    print(f"📡 地址: http://127.0.0.1:{PORT}")
    print(f"🌐 门户: http://127.0.0.1:{PORT}/")
    print(f"📊 日报: http://127.0.0.1:{PORT}/reports/daily_YYYY-MM-DD.html")
    print(f"按 Ctrl+C 停止...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
