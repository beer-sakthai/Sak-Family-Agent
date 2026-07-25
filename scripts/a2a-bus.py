#!/usr/bin/env python3
"""Family A2A Bus — agents send/receive messages"""
import json, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Lock

MSG_FILE = "/opt/data/profiles/sakthai/cache/a2a_messages.json"
lock = Lock()

def load_msgs():
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE) as f:
            return json.load(f)
    return []

def save_msgs(msgs):
    with lock:
        with open(MSG_FILE, 'w') as f:
            json.dump(msgs[-100:], f)  # keep last 100

class A2AHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        
        if self.path == '/send':
            msg = {
                'from': body.get('from', 'unknown'),
                'to': body.get('to', 'all'),
                'type': body.get('type', 'message'),
                'content': body.get('content', ''),
                'timestamp': time.time()
            }
            msgs = load_msgs()
            msgs.append(msg)
            save_msgs(msgs)
            self.send_json({'status': 'ok', 'id': len(msgs)-1})
            
        elif self.path == '/inbox':
            agent = body.get('agent', '')
            msgs = load_msgs()
            inbox = [m for m in msgs if m['to'] in [agent, 'all']]
            self.send_json({'messages': inbox[-20:]})
            
        elif self.path == '/status':
            msgs = load_msgs()
            agents = set(m['from'] for m in msgs)
            self.send_json({'agents': list(agents), 'total_msgs': len(msgs)})
    
    def send_json(self, d):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

if __name__ == '__main__':
    port = 3005
    print(f'Family A2A Bus on port {port}')
    HTTPServer(('0.0.0.0', port), A2AHandler).serve_forever()
