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
    return {
        "Authorization": auth if auth else "",
        "Content-Type": "application/json; charset=UTF-8",
        "Ar-Origin": "https://6win598.com", "Origin": "https://6win598.com",
        "Referer": "https://6win598.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    }

@app.route('/')
def home():
    return "AI Wave Sniper Elite Pro Server is Running!"

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
        r = s.post(BASE_URL + "Login", headers=get_headers(), json=body, timeout=10, verify=not IGNORE_SSL)
        res = r.json()
    except Exception as e:
        return jsonify(ok=False, error="API Timeout or Error: " + str(e))
        
    if res.get("code") == 0:
        tok = res["data"].get("token", "")
        th = res["data"].get("tokenHeader", "Bearer ")
        auth_header = f"{th}{tok}"
        
        info = {}
        try:
            ib = {"language": 0, "random": "9078efc98754430e92e51da59eb2563c"}
            ib["signature"] = sign_md5_original(ib).upper(); ib["timestamp"] = int(time.time())
            headers_info = get_headers()
            headers_info["Authorization"] = auth_header
            ir = s.post(BASE_URL + "GetUserInfo", headers=headers_info, json=ib, timeout=10, verify=not IGNORE_SSL).json()
            if ir.get("code") == 0:
                info = ir["data"]
        except: pass
        
        return jsonify(ok=True, token=auth_header, info=info)
    return jsonify(ok=False, error=res.get("msg", "Login failed"))

@app.route('/api/balance', methods=['GET', 'POST'])
def balance():
    s = requests.Session()
    b = {"language": 0, "random": "9078efc6f3794bf49f257d07937d1a29"}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetBalance", headers=get_headers(), json=b, timeout=10, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            d = res.get("data", {})
            amt = d.get("Amount") or d.get("amount") or 0
            return jsonify(ok=True, balance=float(amt))
        return jsonify(ok=False, error=res.get("msg", "err"))
    except Exception as e:
        return jsonify(ok=False, error=str(e))

def fetch_page(s, page):
    b = {"pageSize": 100, "pageNo": page, "typeId": 30, "language": 7, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper()
    b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetNoaverageEmerdList", headers=get_headers(), json=b, timeout=4, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            return res.get("data", {}).get("list", [])
    except: pass
    return []

@app.route('/api/draws', methods=['GET', 'POST'])
def draws():
    s = requests.Session()
    all_list = []
    seen = set()
    
    # 🔥 1000 ခုပဲ ဆွဲမယ် (Page 10 အထိ) - Vercel Timeout မဖြစ်စေရန်
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda p: fetch_page(s, p), range(1, 11)))
        
    for lst in results:
        for item in lst:
            period = item.get("issueNumber")
            if period and period not in seen:
                seen.add(period)
                all_list.append(item)
                
    all_list.sort(key=lambda x: str(x.get("issueNumber", "")), reverse=True)
    
    if not all_list:
        return jsonify(ok=False, error="API မှ Data ယူ၍မရပါ။ ခဏနေမှ ပြန်ကြိုးစားပါ။")
        
    return jsonify(ok=True, draws=all_list)

@app.route('/api/result', methods=['GET', 'POST'])
def result():
    s = requests.Session()
    period = request.args.get('period')
    b = {"pageSize": 20, "typeId": 30, "language": 7, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
    try:
        res = s.post(BASE_URL + "GetNoaverageEmerdList", headers=get_headers(), json=b, timeout=10, verify=not IGNORE_SSL).json()
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
    s = requests.Session()
    d = request.json
    side = d.get('side')
    amount = int(d.get('amount'))

    issue_b = {"typeId": 30, "language": 0, "random": rnd()}
    issue_b["signature"] = sign_md5_original(issue_b).upper()
    issue_b["timestamp"] = int(time.time())
    
    try:
        issue_res = s.post(BASE_URL + "GetGameIssue", headers=get_headers(), json=issue_b, timeout=5, verify=not IGNORE_SSL).json()
        if issue_res.get("code") != 0:
            return jsonify(ok=False, error="Failed to get current period")
        period = issue_res.get("data", {}).get("issueNumber")
    except Exception as e:
        return jsonify(ok=False, error="Period Error: " + str(e))

    unit = compute_unit(amount)
    count = max(1, amount // unit)
    sel = 13 if side == "B" else 14
    b = {"typeId": 30, "issuenumber": period, "language": 0,
         "gameType": 2, "amount": unit, "betCount": count,
         "selectType": sel, "random": rnd()}
    b["signature"] = sign_md5_original(b).upper()
    b["timestamp"] = int(time.time())
    
    try:
        res = s.post(BASE_URL + "GameBetting", headers=get_headers(), json=b, timeout=8, verify=not IGNORE_SSL).json()
        if res.get("code") == 0:
            return jsonify(ok=True, period=period)
        return jsonify(ok=False, error=res.get("msg", "Bet failed"))
    except Exception as e:
        return jsonify(ok=False, error="Bet Error: " + str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
