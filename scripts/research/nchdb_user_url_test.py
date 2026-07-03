
import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run_intercept():
    # 用戶提供的 URL
    target_url = "https://nchdb.boch.gov.tw/assets/advanceSearch?limit=12&offset=0&query=%7B%22assetsClassifyType%22:null,%22searchType%22:false,%22classifyCode%22:%5B%222.1%22%5D,%22belongCity%22:%2216%22,%22govInstitutionCode%22:%22700%22,%22belongCityId%22:null,%22assetsTypeCode%22:%5B%5D,%22assetsClassifyCode%22:%5B%222.1.1%22%5D,%22buildingYearCode%22:%5B%5D%7D&sort=id&order=desc&classifyCode=2.1"
    
    print(f"🚀 啟動 Playwright 監聽用戶提供 URL...")
    
    output_dir = "data/research/nchdb_intercept"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 設置 User Agent 模仿真實瀏覽器
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        captured_count = 0

        async def check_response(response):
            nonlocal captured_count
            url = response.url
            # 觀察所有回傳 JSON 的端點
            if "api" in url:
                try:
                    ct = response.headers.get("content-type", "")
                    if "application/json" in ct:
                        body = await response.json()
                        filepath = os.path.join(output_dir, f"user_url_capture_{captured_count}.json")
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump({"url": url, "data": body}, f, ensure_ascii=False, indent=2)
                        print(f"✅ 捕獲 API 請求: {url[:80]}...")
                        captured_count += 1
                except:
                    pass

        page.on("response", check_response)

        # 導向用戶提供的特定搜尋結果頁面
        await page.goto(target_url, wait_until="networkidle")
        
        # 等待一段時間讓動態選單與資料載入完全
        print("⏳ 等待 5 秒讓資料載入完成...")
        await asyncio.sleep(5)
        
        await browser.close()
        
    print(f"🎉 任務結束！共捕獲 {captured_count} 個 JSON 資料包。")

if __name__ == "__main__":
    asyncio.run(run_intercept())
