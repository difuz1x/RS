import json
import datetime
import jwt
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET_KEY = "my-super-secret-key-which-is-32bytes!"
ALGORITHM  = "HS256"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE  = os.path.join(BASE_DIR, "login_log.json")

with open(os.path.join(BASE_DIR, "users.json")) as f:
    USERS = json.load(f)

def save_users():
    with open(os.path.join(BASE_DIR, "users.json"), "w") as f:
        json.dump(USERS, f, indent=2)

def log_attempt(ip, username, success):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    logs.append({
        "time":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip":      ip,
        "username": username,
        "success": success
    })
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def create_token(data, expires_delta):
    payload = data.copy()
    now = datetime.datetime.now(datetime.timezone.utc)
    payload["iat"] = now
    payload["exp"] = now + expires_delta
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_admin_payload(headers):
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, "Missing token"
    try:
        payload = jwt.decode(auth.split(" ", 1)[1], SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return None, "Admins only"
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

class AuthHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[AUTH] {self.client_address[0]} {args[0]} {args[1]}", flush=True)

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        if self.path == "/users":
            self.handle_get_users()
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        routes = {
            "/login":       self.handle_login,
            "/refresh":     self.handle_refresh,
            "/delete_user": self.handle_delete_user,
            "/add_user":    self.handle_add_user,
            "/change_role": self.handle_change_role,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_json(404, {"error": "Not found"})

    def handle_login(self):
        body     = self.read_body()
        username = body.get("username", "unknown")
        password = body.get("password")
        print(f"[AUTH] {self.client_address[0]} -> /login user={username}", flush=True)
        user = USERS.get(username)
        if not user or user["password"] != password:
            log_attempt(self.client_address[0], username, False)
            self.send_json(401, {"error": "Invalid credentials"})
            return
        log_attempt(self.client_address[0], username, True)
        access_token = create_token(
            {"sub": username, "role": user["role"]},
            datetime.timedelta(minutes=30)
        )
        refresh_token = create_token(
            {"sub": username, "type": "refresh"},
            datetime.timedelta(days=7)
        )
        self.send_json(200, {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "bearer",
            "role":          user["role"]
        })

    def handle_refresh(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self.send_json(401, {"error": "Missing token"})
            return
        try:
            payload = jwt.decode(auth.split(" ", 1)[1], SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                self.send_json(400, {"error": "Not a refresh token"})
                return
            user = USERS.get(payload["sub"])
            new_access = create_token(
                {"sub": payload["sub"], "role": user["role"]},
                datetime.timedelta(minutes=30)
            )
            self.send_json(200, {"access_token": new_access, "token_type": "bearer"})
        except jwt.ExpiredSignatureError:
            self.send_json(401, {"error": "Refresh token expired"})
        except jwt.InvalidTokenError:
            self.send_json(401, {"error": "Invalid token"})

    def handle_get_users(self):
        payload, err = get_admin_payload(self.headers)
        if err:
            self.send_json(403, {"error": err})
            return
        users_info = [{"username": u, "role": USERS[u]["role"]} for u in USERS]
        self.send_json(200, {"users": users_info})

    def handle_delete_user(self):
        payload, err = get_admin_payload(self.headers)
        if err:
            self.send_json(403, {"error": err})
            return
        body   = self.read_body()
        target = body.get("username")
        if not target or target not in USERS:
            self.send_json(404, {"error": f"User '{target}' not found"})
            return
        if target == payload["sub"]:
            self.send_json(400, {"error": "Cannot delete yourself"})
            return
        del USERS[target]
        save_users()
        print(f"[AUTH] Admin {payload['sub']} deleted user {target}", flush=True)
        self.send_json(200, {"message": f"User '{target}' deleted"})

    def handle_add_user(self):
        payload, err = get_admin_payload(self.headers)
        if err:
            self.send_json(403, {"error": err})
            return
        body     = self.read_body()
        username = body.get("username", "").strip()
        password = body.get("password", "").strip()
        role     = body.get("role", "user")
        if not username or not password:
            self.send_json(400, {"error": "Username and password required"})
            return
        if username in USERS:
            self.send_json(400, {"error": f"User '{username}' already exists"})
            return
        if role not in ("user", "admin"):
            self.send_json(400, {"error": "Role must be 'user' or 'admin'"})
            return
        USERS[username] = {"password": password, "role": role}
        save_users()
        print(f"[AUTH] Admin {payload['sub']} added user {username} (role={role})", flush=True)
        self.send_json(200, {"message": f"User '{username}' added"})

    def handle_change_role(self):
        payload, err = get_admin_payload(self.headers)
        if err:
            self.send_json(403, {"error": err})
            return
        body     = self.read_body()
        target   = body.get("username")
        new_role = body.get("role")
        if not target or target not in USERS:
            self.send_json(404, {"error": f"User '{target}' not found"})
            return
        if new_role not in ("user", "admin"):
            self.send_json(400, {"error": "Role must be 'user' or 'admin'"})
            return
        USERS[target]["role"] = new_role
        save_users()
        print(f"[AUTH] Admin {payload['sub']} changed role of {target} to {new_role}", flush=True)
        self.send_json(200, {"message": f"Role of '{target}' changed to '{new_role}'"})

if __name__ == "__main__":
    host = socket.gethostbyname(socket.gethostname())
    server = HTTPServer(("0.0.0.0", 8080), AuthHandler)
    print(f"Auth server started on {host}:8080")
    server.serve_forever()