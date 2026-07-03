
import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

async def sniff_nchdb_proxy():
    print("🕵️ 啟動 NCHDB 深度流量監聽器 (Sniffer)...")
    
    output_dir = "data/research/nchdb_sniff"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # 使用帶介面的模式或大視窗以確保圖層加載
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        captured_data = []

        async def handle_response(response):
            url = response.url
            # 監聽重點：MapServer, WFS, WMS, PBF (向量圖磚) 或大型 JSON
            target_patterns = [
                "MapServer", "FeatureServer", "wfs", "wms", "tgos", "ArcGIS", 
                "vector", ".pbf", "api/v2/assets"
            ]
            
            if any(p in url for p in target_patterns):
                try:
                    ct = response.headers.get("content-type", "")
                    # 攔截 JSON 或 向量/圖片 資訊
                    if "json" in ct or "application/x-protobuf" in ct or "text/xml" in ct:
                        print(f"🎯 攔截到目標流量: {url[:100]}...")
                        
                        try:
                            # 嘗試讀取內容 (非二進位)
                            if "json" in ct:
                                body = await response.json()
                            else:
                                body = {"type": "binary/xml", "info": "Captured but not parsed"}
                                
                            filename = f"sniff_{len(captured_data)}.json"
                            with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                                json.dump({"url": url, "headers": response.headers, "data": body}, f, ensure_ascii=False, indent=2)
                            captured_data.append(url)
                        except:
                            pass
                except:
                    pass

        page.on("response", handle_response)

        # 第一步：先去首頁建立 Session
        print("1️⃣ 建立 Session: 瀏覽首頁...")
        await page.goto("https://nchdb.boch.gov.tw/", wait_until="networkidle")
        await asyncio.sleep(2)

        # 第二步：前往進階搜尋 (建立搜尋狀態)
        print("2️⃣ 建立狀態: 進入進階搜尋頁面...")
        await page.goto("https://nchdb.boch.gov.tw/assets/advanceSearch/archaeologicalSite", wait_until="networkidle")
        await asyncio.sleep(3)

        # 第三步：跳轉至地圖頁面 (試圖解決 NaN 錯誤)
        print("3️⃣ 核心捕獲: 進入地圖探索頁面...")
        await page.goto("https://nchdb.boch.gov.tw/assets/map", wait_until="networkidle")
        
        # 嘗試點擊地圖上的「圖層管理」- 這裡需要精確的 CSS，我們先等待網頁自動加載
        print("⏳ 等待 15 秒進行圖層渲染與流量監聽...")
        await page.wait_for_timeout(15000)

        # 這裡我們可以嘗試做一些「地圖縮放」，觸發新的點位請求
        print("🔍 執行地圖縮放動作以觸發新請求...")
        await page.mouse.wheel(0, -500) # 向上捲動等於放大地圖
        await page.wait_for_timeout(5000)

        await browser.close()
        
    print(f"\n✅ 監聽結束。共捕獲 {len(captured_data)} 個目標封包。")
    print(f"📂 資料存放在: {output_dir}")

if __name__ == "__main__":
    asyncio.run(sniff_nchdb_proxy())
