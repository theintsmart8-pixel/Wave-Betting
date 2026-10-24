from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, hashlib, time, json, uuid

app = Flask(__name__)
CORS(app)

BASE_URL = "https://6lotteryapi.com/api/webapi/"
IGNORE_SSL = True
sessions = {}

def sign_md5_original(data: dict) -> str:
    exclude = ("signature", "timestamp", "track", "xosoBettingData")
    filtered = {}
    for k, v in data.items():
        if k in exclude: continue
        if v is None or v == "": continue
        filtered[k] = v
    sorted_data = {k: filtered[k] for k in sorted(filtered.keys())}
    json_str = json.dumps(sorted_data, separators=(',', ':'))
    return hashlib.md5(json_str.encode("utf-8")).hexdigest().upper()

def rnd():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:32]

def get_sess():
    tok = request.headers.get('X-Session') or request.args.get('token')
    return sessions.get(tok)

def compute_unit(amt):
    s = str(int(amt))
    tz = len(s) - len(s.rstrip('0'))
    return {4: 10000, 3: 1000, 2: 100, 1: 10}.get(tz, 10 ** (len(s) - 1))

@app.route('/')
def home():
    return "Bet API Server is Running!"

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    phone, pwd = d.get('phone'), d.get('password')
    s = requests.Session()
    body = {
        "username": "95" + phone, "pwd": pwd, "phonetype": 1,
        "logintype": "mobile", "packId": "",
        "deviceId": "5dcab3e06db88a206975e91ea6ac7c87",
        "language": 7, "random": rnd(),
    }
    body["signature"] = sign_md5_original(body).upper()
    body["timestamp"] = int(time.time())
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Ar-Origin": "https://6win598.com", "Origin": "https://6win598.com",
        "Referer": "https://6win598.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    }
    try:
        r = s.post(BASE_URL + "Login", headers=headers, json=body, timeout=15, verify=not IGNORE_SSL)
        res = r.json()
    except Exception as e:
        return jsonify(ok=False, error=str(e))
        
    if res.get("code") == 0:
        tok = res["data"].get("token", "")
        th = res["data"].get("tokenHeader", "Bearer ")
        s.headers.update({
            "Authorization": f"{th}{tok}",
            "Content-Type": "application/json; charset=UTF-8",
            "Ar-Origin": "https://6win598.com", "Origin": "https://6win598.com",
            "Referer": "https://6win598.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        })
        token = uuid.uuid4().hex
        sessions[token] = s
        
        info = {}
        try:
            ib = {"language": 0, "random": "9078efc98754430e92e51da59eb2563c"}
            ib["signature"] = sign_md5_original(ib).upper(); ib["timestamp"] = int(time.time())
            ir = s.post(BASE_URL + "GetUserInfo", json=ib, timeout=12, verify=not IGNORE_SSL).json()
            if ir.get("code") == 0:
                info = ir["data"]
        except: pass
        return jsonify(ok=True, token=token, info=info)
    return jsonify(ok=False, error=res.get("msg", "Login failed"))

@app.route('/api/balance')
def balance():
    s = get_sess()
    if not s: return jsonify(ok=False, error="auth"), 401
    b = {"language": 0, "random": "9078efc6f3794bf49f257d07937d1a29"}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetBalance", json=b, timeout=20, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            d = res.get("data", {})
            amt = d.get("Amount") or d.get("amount") or 0
            return jsonify(ok=True, balance=float(amt))
        return jsonify(ok=False, error=res.get("msg", "err"))
    except Exception as e:
        return jsonify(ok=False, error=str(e))

@app.route('/api/issue')
def issue():
    s = get_sess()
    if not s: return jsonify(ok=False, error="auth"), 401
    b = {"typeId": 30, "language": 0, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetGameIssue", json=b, timeout=12, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            return jsonify(ok=True, issue=res["data"].get("issueNumber"))
        return jsonify(ok=False, error=res.get("msg", "err"))
    except Exception as e:
        return jsonify(ok=False, error=str(e))

@app.route('/api/draws')
def draws():
    s = get_sess()
    if not s: return jsonify(ok=False, error="auth"), 401
    b = {"pageSize": 10000, "pageNo": 1, "typeId": 30, "language": 7, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetNoaverageEmerdList", json=b, timeout=60, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            return jsonify(ok=True, draws=res.get("data", {}).get("list", []))
        return jsonify(ok=False, error=res.get("msg", "err"))
    except Exception as e:
        return jsonify(ok=False, error=str(e))

@app.route('/api/result')
def result():
    s = get_sess()
    if not s: return jsonify(ok=False, error="auth"), 401
    period = request.args.get('period')
    b = {"pageSize": 20, "typeId": 30, "language": 7, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetNoaverageEmerdList", json=b, timeout=12, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            for d in res.get("data", {}).get("list", []):
                if str(d.get("issueNumber")) == str(period):
                    n = int(str(d.get("number", "0"))) % 10
                    return jsonify(ok=True, number=n, bs="B" if n >= 5 else "S")
            return jsonify(ok=False, pending=True)
        return jsonify(ok=False, error=res.get("msg", "err"))
    except Exception as e:
        return jsonify(ok=False, error=str(e))

@app.route('/api/bet', methods=['POST'])
def bet():
    s = get_sess()
    if not s: return jsonify(ok=False, error="auth"), 401
    d = request.json
    period, side, amount = d.get('period'), d.get('side'), int(d.get('amount'))
    unit = compute_unit(amount)
    count = max(1, amount // unit)
    sel = 13 if side == "B" else 14
    b = {"typeId": 30, "issuenumber": period, "language": 0,
         "gameType": 2, "amount": unit, "betCount": count,
         "selectType": sel, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GameBetting", json=b, timeout=30, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            return jsonify(ok=True)
        return jsonify(ok=False, error=res.get("msg", "Bet failed"))
    except Exception as e:
        return jsonify(ok=False, error=str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
