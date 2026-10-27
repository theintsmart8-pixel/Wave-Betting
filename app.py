from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, hashlib, time, json

app = Flask(__name__)
CORS(app)

BASE_URL = "https://6lotteryapi.com/api/webapi/"
CF_WORKER_URL = "https://billowing-rice-4e18.theintsmart8.workers.dev/?url=" # Proxy Fallback
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
    return "Advanced AI V2 is Running!"

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

@app.route('/api/predict_v2', methods=['POST'])
def predict_v2():
    s = requests.Session()
    all_list = []
    API_URL = BASE_URL + "GetNoaverageEmerdList"
    
    # Draw 200 ခုကို တိုက်ရိုက် ဆွဲမယ်၊ မရရင် Proxy ကနေ ဆွဲမယ်
    for page in range(1, 3): # 2 မျက်နှာပဲ ဆွဲမယ် (Draw 200)
        b = {"pageSize": 100, "pageNo": page, "typeId": 30, "language": 7, "random": rnd()}
        b["signature"] = sign_md5_original(b).upper()
        b["timestamp"] = int(time.time())
        
        success = False
        # ၁။ တိုက်ရိုက် ကြိုးစားမယ်
        try:
            res = s.post(API_URL, headers=get_headers(), json=b, timeout=3, verify=not IGNORE_SSL).json()
            if res.get("code") == 0 and res.get("data", {}).get("list"):
                all_list.extend(res.get("data", {}).get("list", []))
                success = True
        except:
            pass
            
        # ၂။ တိုက်ရိုက် မရရင် Cloudflare Worker ကနေ ဖြတ်ဆွဲမယ်
        if not success:
            try:
                proxy_url = CF_WORKER_URL + API_URL
                res2 = s.post(proxy_url, headers=get_headers(), json=b, timeout=5, verify=not IGNORE_SSL).json()
                if res2.get("code") == 0:
                    all_list.extend(res2.get("data", {}).get("list", []))
            except:
                pass
                
    if not all_list: 
        return jsonify(ok=False, error="API Data မရပါ။ (Vercel Timeout သို့မဟုတ် Block ဖြစ်နေပါသည်)")
    
    all_list.sort(key=lambda x: str(x.get("issueNumber", "")), reverse=True)
    bsSeq = []
    for d in all_list:
        try:
            n = int(str(d.get("number")).strip()) % 10
            bsSeq.append('B' if n >= 5 else 'S')
        except: pass

    if len(bsSeq) < 50: 
        return jsonify(ok=False, error="Data မလုံလောက်ပါ။ ခဏနေမှ ပြန်စမ်းပါ။")

    # ==========================================
    # ADVANCED AI V2 LOGIC
    # ==========================================
    
    # 1. Pattern Recognition
    patternLengths = [5, 4, 3]
    bestPatternConf = 0
    bestPatternPred = 'B'
    
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
            
            if conf > bestPatternConf:
                bestPatternConf = conf
                bestPatternPred = pred
            if bestPatternConf >= 80: break

    # 2. Wave Trend (Last 20 draws)
    recent20 = bsSeq[:20]
    b_count = recent20.count('B')
    s_count = recent20.count('S')
    trendPred = 'B' if b_count >= s_count else 'S'
    trendConf = (max(b_count, s_count) / 20) * 100

    # 3. Streak Analysis
    current_streak_val = bsSeq[0]
    streak_len = 0
    for val in bsSeq:
        if val == current_streak_val: streak_len += 1
        else: break
        
    streak_break = 0
    streak_continue = 0
    for i in range(1, len(bsSeq) - streak_len):
        if "".join(bsSeq[i:i+streak_len]) == "".join(bsSeq[0:streak_len]):
            if bsSeq[i-1] == current_streak_val: streak_continue += 1
            else: streak_break += 1
            
    streak_total = streak_break + streak_continue
    if streak_total > 0:
        if streak_break > streak_continue:
            streakPred = 'S' if current_streak_val == 'B' else 'B'
            streakConf = (streak_break / streak_total) * 100
        else:
            streakPred = current_streak_val
            streakConf = (streak_continue / streak_total) * 100
    else:
        streakPred = trendPred
        streakConf = 50

    # 4. Combine Scores
    final_b_score = 0
    final_s_score = 0
    
    if bestPatternPred == 'B': final_b_score += (bestPatternConf * 0.5)
    else: final_s_score += (bestPatternConf * 0.5)

    if trendPred == 'B': final_b_score += (trendConf * 0.3)
    else: final_s_score += (trendConf * 0.3)

    if streakPred == 'B': final_b_score += (streakConf * 0.2)
    else: final_s_score += (streakConf * 0.2)

    if final_b_score > final_s_score:
        final_pred = 'B'
        final_conf = final_b_score
    else:
        final_pred = 'S'
        final_conf = final_s_score

    reason_str = ""
    if final_conf >= 65:
        reason_str = f"Pattern ({bestPatternConf:.0f}%) + Trend ({trendConf:.0f}%) + Streak ({streakConf:.0f}%)"
    else:
        reason_str = "⚠️ ခန့်မှန်းချက် အားနည်းနေပါသည်။ မလောင်းဘဲ နေပါ။"

    return jsonify(
        ok=True, 
        prediction=final_pred, 
        confidence=final_conf, 
        reason=reason_str,
        pattern_info=f"{bestPatternConf:.0f}%", 
        trend_info=f"{trendPred} ({trendConf:.0f}%)",
        streak_info=f"{streak_len} times"
    )

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
