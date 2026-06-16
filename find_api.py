#!/usr/bin/env python3
"""Run this on the server to find video API endpoints for Jimeng and Doubao."""
import requests, re, json, sys

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/jianying_web_ug/activities/static/js/"

results = {}

# ========== 1. Check doubao page for video data ==========
print("=== 1. Doubao page ===")
try:
    h = requests.get(
        "https://www.doubao.com/video-sharing?share_id=47659942068203522&video_id=v0269cg10004d8oi49aljhtbaaqu8l70&share_scene=video_viewer",
        headers=HEADERS, timeout=15).text
    print(f"  Length: {len(h)}")
    # Check all window.* assignments
    for m in re.finditer(r'window\.([a-zA-Z0-9_]+)\s*=\s*(\{.*?\});', h):
        name = m.group(1)
        data = m.group(2)[:100]
        print(f"  window.{name}: {data}...")
    # Check for __NUXT__ / __INITIAL_STATE__
    for pat_name, pat in [("__NUXT__", r'window\.__NUXT__\s*=\s*(\{.*?\});'),
                          ("__INITIAL_STATE__", r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});'),
                          ("RENDER_DATA", r'<script id="RENDER_DATA"[^>]*>(.*?)</script>')]:
        m = re.search(pat, h, re.DOTALL)
        if m:
            print(f"  Found {pat_name} in page!")
            print(f"    First 200: {m.group(1)[:200]}")
    # Find any mp4/m3u8 references
    for u in set(re.findall(r'https?://[^"'"'"'<>]*(?:\.mp4|\.m3u8)[^"'"'"'<>]*', h)):
        print(f"  Video URL found: {u[:120]}")
except Exception as e:
    print(f"  Error: {e}")

# ========== 2. Check Jimeng JS bundles for API patterns ==========
print("\n=== 2. Jimeng JS bundles ===")
chunks = ["4761.fb0c9f48.js", "6106.f737ca47.js", "3366.01551ca3.js"]
for chunk in chunks:
    try:
        js = requests.get(BASE_URL + chunk, headers=HEADERS, timeout=10).text
        # Search for API hostnames and paths
        found = []
        for pat in [r'https?://jimeng[^"'"'"'\s]*', r'https?://api[^"'"'"'\s]*dreamina[^"'"'"'\s]*',
                     r'https?://[^"'"'"'\s]*jianying[^"'"'"'\s]*api[^"'"'"'\s]*',
                     r'"/api/[^"]+"', r"'/api/[^']+'",
                     r'baseURL[=:]\s*["'"'"']([^"'"'"']+)["'"'"']',
                     r'baseUrl[=:]\s*["'"'"']([^"'"'"']+)["'"'"']']:
            for m in set(re.findall(pat, js)):
                cleaned = m.strip("'\"")
                if len(cleaned) > 5 and 'mon' not in cleaned:
                    found.append(cleaned)
        if found:
            print(f"  {chunk} ({len(js)} bytes): {list(set(found))[:5]}")
    except Exception as e:
        print(f"  {chunk}: Error - {str(e)[:40]}")

# ========== 3. Try external APIs ==========
print("\n=== 3. Testing external APIs ===")
test_urls = [
    "https://jimeng.jianying.com/s/4y39oB538Zc/?t=210",
    "https://www.doubao.com/video-sharing?share_id=47659942068203522&video_id=v0269cg10004d8oi49aljhtbaaqu8l70",
]
api_endpoints = [
    "https://api.limour.top/api/parse",
]
for api in api_endpoints:
    for test_url in test_urls:
        try:
            resp = requests.post(api, json={"url": test_url}, headers=HEADERS, timeout=15)
            print(f"  {api} ({test_url[:40]}...): {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    if data.get("data", {}).get("urls"):
                        print(f"    SUCCESS! URL: {data['data']['urls'][0]['url'][:80]}")
                    elif data.get("url"):
                        print(f"    SUCCESS! URL: {data['url'][:80]}")
                    else:
                        print(f"    Response: {str(data)[:200]}")
                else:
                    print(f"    Content: {resp.text[:200]}")
        except Exception as e:
            print(f"  {api} ({test_url[:40]}...): Error - {str(e)[:40]}")
