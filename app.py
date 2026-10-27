from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, hashlib, time, json
from concurrent.futures import ThreadPoolExecutor

# Vercel က ဒီနေရာမှာ 'app' လို့ပဲ ဖြစ်ရမယ်လို့ တင်းကျပ်ထားပါတယ်
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
    return "6Lottery AI Backend is Running Successfully!"

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
        r = s.post(BASE_URL + "Login", headers=get_headers(), json=body, timeout=9, verify=not IGNORE_SSL)
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

        return jsonify(ok=False, error=f"Bal: {res.get('msg')} / Info: {res2.get('msg')}")
    except Exception as e:
        return jsonify(ok=False, error="Timeout")

@app.route('/api/predict', methods=['POST'])
def predict():
    s = requests.Session()
    def fetch_page(page):
        b = {"pageSize": 100, "pageNo": page, "typeId": 30, "language": 7, "random": rnd()}
        b["signature"] = sign_md5_original(b).upper(); b["timestamp"] = int(time.time())
        try:
            res = s.post(BASE_URL + "GetNoaverageEmerdList", headers=get_headers(), json=b, timeout=5, verify=not IGNORE_SSL).json()
            if res.get("code") == 0: return res.get("data", {}).get("list", [])
        except: pass
        return []

    all_list = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(fetch_page, range(1, 7)))
        
    for lst in results: all_list.extend(lst)
    if not all_list: return jsonify(ok=False, error="API Blocked or Timeout")
    
    all_list.sort(key=lambda x: str(x.get("issueNumber", "")), reverse=True)
    bsSeq = []
    for d in all_list:
        try:
            n = int(str(d.get("number")).strip()) % 10
            bsSeq.append('B' if n >= 5 else 'S')
        except: pass

    patternLengths = [5, 4, 3]
    bestResult = None
    for plen in patternLengths:
        currentPattern = "".join(bsSeq[:plen])
        totalMatches, bigNext, smallNext = 0, 0, 0
        for i in range(1, len(bsSeq) - plen):
            if "".join(bsSeq[i:i+plen]) == currentPattern:
                totalMatches += 1
                if bsSeq[i-1] == 'B': bigNext += 1
                else: smallNext += 1
        if totalMatches > 0:
            if bigNext > smallNext: pred, conf = 'B', (bigNext / totalMatches) * 100
            elif smallNext > bigNext: pred, conf = 'S', (smallNext / totalMatches) * 100
            else: continue
            
            if not bestResult or conf > bestResult['conf']:
                bestResult = {'pred': pred, 'conf': conf}
            if bestResult['conf'] >= 75: break

    if not bestResult: bestResult = {'pred': 'B', 'conf': 50.0}

    return jsonify(ok=True, prediction=bestResult['pred'], confidence=bestResult['conf'])

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
