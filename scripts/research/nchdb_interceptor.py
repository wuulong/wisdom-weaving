
import asyncio
import json
import os
from playwright.async_api import async_playwright

async def intercept_nchdb():
    print("🚀 啟動 Playwright 攔截器...")
    
    # 確保儲存目錄存在
    output_dir = "data/research/nchdb_intercept"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # 啟動瀏覽器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 定義攔截邏輯
        captured_files = []

        async def handle_response(response):
            # 我們過濾可能是資料來源的 URL
            url = response.url
            if "api" in url or ".json" in url or "assets" in url:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        print(f"✨ 發現 JSON 端點: {url}")
                        data = await response.json()
                        filepath = os.path.join(output_dir, f"capture_{len(captured_files)}.json")
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump({"url": url, "data": data}, f, ensure_ascii=False, indent=2)
                        captured_files.append(url)
                except Exception as e:
                    # 有些 response 可能無法讀取 (例如 404 or empty)
                    pass

        page.on("response", handle_response)

        print("🌐 正在進入 NCHDB 地圖頁面...")
        # 進入地圖頁面
        await page.goto("https://nchdb.boch.gov.tw/assets/map", wait_until="networkidle")
        
        print("⏳ 等待 10 秒讓地圖層載入...")
        await page.wait_for_timeout(10000)

        # 嘗試點擊按鈕或觸發更多載入 (如果有需要)
        # 這裡我們觀察初步進入時會抓到什麼
        
        await browser.close()
        
    print(f"\n✅ 攔截結束。共發現 {len(captured_files)} 個 JSON 封包。")
    print(f"📂 原始資料已存在: {output_dir}")

if __name__ == "__main__":
    asyncio.run(intercept_nchdb())
