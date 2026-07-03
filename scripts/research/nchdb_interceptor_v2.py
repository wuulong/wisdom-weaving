
import asyncio
import json
import os
from playwright.async_api import async_playwright

async def intercept_nchdb_search():
    print("🚀 啟動 NCHDB 搜尋攔截器 (v2)...")
    
    output_dir = "data/research/nchdb_intercept"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        captured = []

        async def handle_response(response):
            url = response.url
            if "api" in url:
                try:
                    ct = response.headers.get("content-type", "")
                    if "application/json" in ct:
                        data = await response.json()
                        # 我們觀察回傳的 JSON 結構，看是否有 'caseName' 或 'assets'
                        filename = f"search_capture_{len(captured)}.json"
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump({"url": url, "data": data}, f, ensure_ascii=False, indent=2)
                        print(f"✨ 攔截成功: {filename} (URL: {url[:60]}...)")
                        captured.append(url)
                except:
                    pass

        page.on("response", handle_response)

        print("🌐 進入進階搜尋頁面...")
        await page.goto("https://nchdb.boch.gov.tw/assets/advanceSearch/archaeologicalSite", wait_until="networkidle")

        print("🖱️ 尋找並點擊搜尋按鈕...")
        # 根據 Angular SPA 的特性，按鈕通常有特定的 class 或文字
        # 這裡嘗試點擊包含 "查詢" 文字的按鈕
        try:
            # 等待按鈕出現
            search_button = page.locator("button:has-text('查詢')")
            await search_button.click()
            print("✅ 點擊查詢按鈕成功")
        except Exception as e:
            print(f"❌ 點擊查詢按鈕失敗: {e}")

        print("⏳ 等待資料回傳...")
        await page.wait_for_timeout(5000)

        await browser.close()
        
    print(f"\n✅ 任務結束。攔截到 {len(captured)} 個可能的 API 封包。")

if __name__ == "__main__":
    asyncio.run(intercept_nchdb_search())
