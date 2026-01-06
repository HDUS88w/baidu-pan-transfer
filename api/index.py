from http.server import BaseHTTPRequestHandler
import json
import time
import hmac
import hashlib
import os

# 配置（从环境变量读取）
APP_KEY = os.environ.get("APP_KEY", "default_app_key_123456")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "default_token_789")

# 内存存储
tasks = {}

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/api/health' or self.path == '/health':
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "service": "baidu-pan-transfer",
                "version": "1.0"
            }).encode())
            return
        
        elif self.path.startswith('/api/task/'):
            task_id = self.path.split('/')[-1]
            task = tasks.get(task_id)
            
            if not task:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "任务不存在"}).encode())
            else:
                self._set_headers()
                self.wfile.write(json.dumps(task).encode())
            return
        
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "路径不存在"}).encode())
    
    def do_POST(self):
        if self.path == '/api/transfer' or self.path == '/transfer':
            # 验证API密钥
            api_key = self.headers.get('X-API-Key')
            if not api_key or api_key != APP_KEY:
                self._set_headers(403)
                self.wfile.write(json.dumps({
                    "error": "无效的API密钥",
                    "tip": "请检查X-API-Key请求头"
                }).encode())
                return
            
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # 验证必要参数
            pan_url = data.get('pan_url')
            if not pan_url:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "缺少pan_url参数"}).encode())
                return
            
            # 创建任务
            task_id = str(int(time.time() * 1000))
            tasks[task_id] = {
                "status": "processing",
                "pan_url": pan_url,
                "created_at": time.time(),
                "webhook_url": data.get('webhook_url'),
                "result": None
            }
            
            # 模拟处理结果
            import threading
            def process_task():
                time.sleep(2)
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = {
                    "direct_link": f"https://transfer.example.com/download/{task_id}",
                    "filename": "文件.zip",
                    "size": "156.8MB",
                    "expire_time": "24小时后"
                }
                
                # 发送Webhook回调
                webhook_url = data.get('webhook_url')
                if webhook_url:
                    self._send_webhook(webhook_url, data.get('webhook_token'), task_id)
            
            thread = threading.Thread(target=process_task)
            thread.daemon = True
            thread.start()
            
            # 立即返回响应
            self._set_headers(202)
            response = {
                "success": True,
                "message": "转存任务已开始处理",
                "task_id": task_id,
                "check_url": f"/api/task/{task_id}",
                "note": "稍后查询任务状态获取结果"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "路径不存在"}).encode())
    
    def _send_webhook(self, webhook_url, token, task_id):
        """发送Webhook回调"""
        try:
            import urllib.request
            task = tasks[task_id]
            payload = {
                "event": "transfer.completed",
                "task_id": task_id,
                "status": task["status"],
                "result": task["result"],
                "timestamp": time.time()
            }
            
            use_token = token if token else WEBHOOK_TOKEN
            signature = hmac.new(
                use_token.encode('utf-8'),
                json.dumps(payload).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'X-Signature': signature
                }
            )
            urllib.request.urlopen(req, timeout=5)
            
        except Exception as e:
            print(f"Webhook发送失败: {str(e)}")
