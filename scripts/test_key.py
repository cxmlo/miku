import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "").split(",")[0].strip()
models = [
    'gemini-flash-lite-latest',
    'gemini-2.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-pro-latest',
    'gemma-4-26b-a4b-it',
    'gemma-4-31b-it',
    'gemini-flash-latest'
]

for m in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "Di 'OK'"}]}]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"[EXITO] {m} -> {text.strip()}")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        try:
            j = json.loads(err)
            msg = j.get('error', {}).get('message', err)
        except:
            msg = err
        print(f"[ERROR {e.code}] {m} -> {msg[:90]}")
    except Exception as e:
        print(f"[EXC] {m} -> {e}")
