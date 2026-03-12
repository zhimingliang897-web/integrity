import urllib.request
try:
    req = urllib.request.Request('http://localhost:5000/progress')
    with urllib.request.urlopen(req, timeout=5) as resp:
        for _ in range(5):
            line = resp.readline().decode('utf-8')
            if line.strip():
                print(line.strip())
except Exception as e:
    print("Error:", e)
