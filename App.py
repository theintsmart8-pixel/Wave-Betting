@app.route('/api/draws', methods=['GET', 'POST'])
def draws():
    s = requests.Session()
    all_list = []
    # 10 ခါ လှမ်းခေါ်ပြီး 1000 ခု ယူမယ်
    for page in range(1, 11):
        b = {"pageSize": 100, "pageNo": page, "typeId": 30, "language": 7, "random": rnd()}
        b["signature"] = sign_md5_original(b).upper()
        b["timestamp"] = int(time.time())
        try:
            res = s.post(BASE_URL + "GetNoaverageEmerdList", headers=get_headers(), json=b, timeout=5, verify=not IGNORE_SSL).json()
            if res.get("code") == 0:
                lst = res.get("data", {}).get("list", [])
                all_list.extend(lst)
                if len(lst) < 100: break
            else: break
        except: break
    return jsonify(ok=True, draws=all_list)
