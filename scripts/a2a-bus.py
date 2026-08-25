#!/usr/bin/env python3
"""Family A2A Bus — agents send/receive messages"""
import json, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Lock

MSG_FILE = "/opt/data/profiles/sakthai/cache/a2a_messages.json"
TASKS_FILE = "/opt/data/profiles/sakthai/cache/a2a_tasks.json"
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

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            data = json.load(f)
            if isinstance(data, dict):
                return list(data.values())
            return data
    return []

def save_tasks(tasks):
    with lock:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)

class A2AHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
        except (json.JSONDecodeError, ValueError) as e:
            self.send_json({'status': 'error', 'message': f'invalid JSON: {e}'})
            return
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)})
            return
        
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
            inbox = [m for m in msgs if m['to'] in {agent, 'all'}]
            self.send_json({'messages': inbox[-20:]})
            
        elif self.path == '/status':
            msgs = load_msgs()
            agents = set(m['from'] for m in msgs)
            self.send_json({'agents': list(agents), 'total_msgs': len(msgs)})

        elif self.path == '/task/create':
            task = {
                'from': body.get('from', 'unknown'),
                'task_id': str(body.get('task_id', '')).strip() or f"task_{int(time.time())}",
                'description': body.get('description', ''),
                'targets': body.get('targets', []),
                'shards': body.get('shards', []),
                'status': 'queued',
                'created': time.time(),
                'updated': time.time(),
            }
            tasks = load_tasks()
            existing = [t for t in tasks if t['task_id'] == task['task_id']]
            if existing:
                existing[0].update(task)
            else:
                tasks.append(task)
            save_tasks(tasks)
            self.send_json({'status': 'ok', 'task_id': task['task_id'], 'shards': len(task['shards'])})
            return

        elif self.path == '/task/list':
            tasks = load_tasks()
            self.send_json({'tasks': tasks, 'count': len(tasks)})
            return

        elif self.path == '/task/status':
            task_id = str(body.get('task_id', '')).strip()
            tasks = load_tasks()
            task = next((t for t in tasks if t['task_id'] == task_id), None)
            if not task:
                self.send_json({'status': 'not_found', 'task_id': task_id})
            else:
                self.send_json({'status': 'ok', 'task': task})

        elif self.path == '/task/claim':
            task_id = str(body.get('task_id', '')).strip()
            shard_id = body.get('shard_id', '')
            agent = body.get('agent', 'unknown')
            tasks = load_tasks()
            task = next((t for t in tasks if t['task_id'] == task_id), None)
            if not task:
                self.send_json({'status': 'error', 'message': f'task {task_id} not found'})
                return
            # Find the shard and try to claim it
            shard = None
            shard_idx = -1
            for i, s in enumerate(task.get('shards', [])):
                # Handle both list and dict shard formats
                sid = s.get('shard_id', s.get('id', i)) if isinstance(s, dict) else i
                if str(sid) == str(shard_id) or sid == shard_id:
                    shard = s
                    shard_idx = i
                    break
            if shard is None and isinstance(shard_id, int):
                # Try numeric index
                if 0 <= shard_id < len(task.get('shards', [])):
                    shard = task['shards'][shard_id]
                    shard_idx = shard_id

            if shard is None:
                self.send_json({'status': 'error', 'message': f'shard {shard_id} not found in task {task_id}'})
                return

            # Normalize shard to dict early so .get / item assignment works
            if not isinstance(shard, dict):
                shard = {'input': shard}
                task['shards'][shard_idx] = shard

            if shard.get('status') == 'claimed':
                self.send_json({'status': 'error', 'message': 'shard already claimed by another agent'})
                return

            # Claim the shard
            shard['status'] = 'claimed'
            shard['claimed_by'] = agent
            shard['claimed_at'] = time.time()
            save_tasks(tasks)
            self.send_json({'status': 'ok', 'task_id': task_id, 'shard_id': shard_id, 'input': shard})

        elif self.path == '/task/complete':
            task_id = str(body.get('task_id', '')).strip()
            shard_id = body.get('shard_id', '')
            agent = body.get('from', 'unknown')
            result = body.get('result', '')
            tasks = load_tasks()
            task = next((t for t in tasks if t['task_id'] == task_id), None)
            if not task:
                self.send_json({'status': 'error', 'message': f'task {task_id} not found'})
                return
            # Find and update the shard
            found = False
            for i, s in enumerate(task.get('shards', [])):
                sid = s.get('shard_id', s.get('id', i)) if isinstance(s, dict) else i
                if str(sid) == str(shard_id) or sid == shard_id:
                    if not isinstance(s, dict):
                        s = {'input': s}
                        task['shards'][i] = s
                    s['status'] = 'completed'
                    s['result'] = result
                    s['completed_at'] = time.time()
                    s['completed_by'] = agent
                    found = True
                    break
            if not found:
                self.send_json({'status': 'error', 'message': f'shard {shard_id} not found in task {task_id}'})
                return
            # Check if all shards are done
            all_done = all((isinstance(s, dict) and s.get('status') == 'completed') for s in task.get('shards', []))
            task['status'] = 'completed' if all_done else 'in_progress'
            task['updated'] = time.time()
            save_tasks(tasks)
            self.send_json({'status': 'ok', 'task_id': task_id, 'shard_id': shard_id, 'all_done': all_done})

        else:
            self.send_json({'status': 'error', 'message': 'unknown endpoint'})
    
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
