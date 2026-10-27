from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, hashlib, time, json
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)

BASE_URL = "https://6lotteryapi.com/api/webapi/"
IGNORE_SSL = True

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

def compute_unit(amt):
    s = str(int(amt))
    tz = len(s) - len(s.rstrip('0'))
    return {4: 10000, 3: 1000, 2: 100, 1: 10}.get(tz, 10 ** (len(s) - 1))

def get_headers():
    auth = request.headers.get('Authorization')
    if not auth:
        auth = request.headers.get('authorization')
    return {
        "Authorization": auth if auth else "",
        "Content-Type": "application/json; charset=UTF-8",
        "Ar-Origin": "https://6win598.com", "Origin": "https://6win598.com",
        "Referer": "https://6win598.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    }

@app.route('/')
def home():
    return "Bet & Login API is Running Successfully!"

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
    
    try:
        r = s.post(BASE_URL + "Login", headers=get_headers(), json=body, timeout=8, verify=not IGNORE_SSL)
        res = r.json()
    except Exception as e:
        return jsonify(ok=False, error="Login Timeout")
        
    if res.get("code") == 0:
        tok = res["data"].get("token", "")
        th = res["data"].get("tokenHeader", "Bearer ")
        if th and not th.endswith(" "): th += " "
        return jsonify(ok=True, token=f"{th}{tok}".strip())
    return jsonify(ok=False, error=res.get("msg", "Login failed"))

@app.route('/api/balance', methods=['POST'])
def balance():
    s = requests.Session()
    b = {"language": 0, "random": "9078efc6f3794bf49f257d07937d1a29"}
    b["signature"] = sign_md5_original(b).upper()
    b["timestamp"] = int(time.time())
    
    try:
        res = s.post(BASE_URL + "GetBalance", headers=get_headers(), json=b, timeout=8, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            d = res.get("data", {})
            amt = d.get("Amount") or d.get("amount") or d.get("balance") or 0
            return jsonify(ok=True, balance=float(amt))

        b2 = {"language": 0, "random": rnd()}
        b2["signature"] = sign_md5_original(b2).upper()
        b2["timestamp"] = int(time.time())
        res2 = s.post(BASE_URL + "GetUserInfo", headers=get_headers(), json=b2, timeout=8, verify=not IGNORE_SSL).json()
        
        if res2.get("code") == 0:
            amt2 = res2.get("data", {}).get("amount", 0)
            return jsonify(ok=True, balance=float(amt2))

        return jsonify(ok=False, error=f"Bal: {res.get('msg')}")
    except Exception as e:
        return jsonify(ok=False, error="Timeout")

# 🔥 AI အတွက် Draw 1000 ကို Vercel ကနေ တိုက်ရိုက် သွားယူပေးမယ့် API
@app.route('/api/fetch_draws', methods=['POST'])
def fetch_draws():
    s = requests.Session()
    
    def fetch_page(page):
        b = {"pageSize": 100, "pageNo": page, "typeId": 30, "language": 7, "random": rnd()}
        b["signature"] = sign_md5_original(b).upper()
        b["timestamp"] = int(time.time())
        try:
            res = s.post(BASE_URL + "GetNoaverageEmerdList", headers=get_headers(), json=b, timeout=4, verify=not IGNORE_SSL).json()
            if res.get("code") == 0: return res.get("data", {}).get("list", [])
        except: pass
        return []

    all_list = []
    # 10 မျက်နှာကို တစ်ပြိုင်နက်တည်း ဆွဲမယ် (အလွန်မြန်)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_page, range(1, 11)))
        
    for lst in results: all_list.extend(lst)
        
    if not all_list:
        return jsonify(ok=False, error="API မှ Data မရပါ။")
        
    all_list.sort(key=lambda x: str(x.get("issueNumber", "")), reverse=True)
    return jsonify(ok=True, draws=all_list)

@app.route('/api/bet', methods=['POST'])
def bet():
    s = requests.Session()
    d = request.json
    side, amount = d.get('side'), int(d.get('amount'))

    issue_b = {"typeId": 30, "language": 0, "random": rnd()}
    issue_b["signature"] = sign_md5_original(issue_b).upper(); issue_b["timestamp"] = int(time.time())
    try:
        issue_res = s.post(BASE_URL + "GetGameIssue", headers=get_headers(), json=issue_b, timeout=5, verify=not IGNORE_SSL).json()
        if issue_res.get("code") != 0: return jsonify(ok=False, error="Period Error")
        period = issue_res.get("data", {}).get("issueNumber")
    except: return jsonify(ok=False, error="Period Timeout")

    unit = compute_unit(amount)
    count = max(1, amount // unit)
    sel = 13 if side == "B" else 14
    b = {"typeId": 30, "issuenumber": period, "language": 0, "gameType": 2, "amount": unit, "betCount": count, "selectType": sel, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GameBetting", headers=get_headers(), json=b, timeout=8, verify=not IGNORE_SSL).json()
        if res.get("code") == 0: return jsonify(ok=True, period=period)
        return jsonify(ok=False, error=res.get("msg", "Bet failed"))
    except: return jsonify(ok=False, error="Bet Timeout")

@app.route('/api/result', methods=['POST'])
def result():
    s = requests.Session()
    d = request.json
    period = d.get('period')
    b = {"pageSize": 20, "typeId": 30, "language": 7, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetNoaverageEmerdList", headers=get_headers(), json=b, timeout=8, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            for item in res.get("data", {}).get("list", []):
                if str(item.get("issueNumber")) == str(period):
                    n = int(str(item.get("number"))) % 10
                    return jsonify(ok=True, bs="B" if n >= 5 else "S", number=n)
        return jsonify(ok=False, pending=True)
    except: return jsonify(ok=False, pending=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
