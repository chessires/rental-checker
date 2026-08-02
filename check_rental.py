import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

URL = "https://rental.aconeco.com/21"
TO_EMAIL = "chessires@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")


def check_availability():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 設定較大的螢幕解析度與真實 User-Agent，避免 mobile 版網頁結構不同
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("正在載入網頁...")
            page.goto(URL, wait_until="networkidle", timeout=30000)
            
            # 等待前端 Vue/React DOM 完全掛載
            page.wait_for_timeout(4000)

            # 抓取頁面上所有按鈕或主要區塊的文字（用於 Debug log）
            buttons = page.locator("button, a.btn, div[role='button']").all_inner_texts()
            clean_buttons = [b.strip() for b in buttons if b.strip()]
            print(f"【Debug】偵測到的按鈕文字列表: {clean_buttons}")

            page_text = page.inner_text("body")

            # 判斷條款：
            # 條件 1：內文或按鈕包含「立即登記」/「開放登記」/「申請」
            # 條件 2：沒有包含「非開放」或「未開放」或「已額滿」
            has_register_keyword = any(kw in page_text for kw in ["立即登記", "開放登記", "線上登記"])
            has_closed_keyword = any(kw in page_text for kw in ["非開放登記時間", "未開放", "暫不開放"])

            print(f"【Debug】包含開放關鍵字: {has_register_keyword} | 包含封閉關鍵字: {has_closed_keyword}")

            # 只要出現開放關鍵字，且封閉關鍵字消失，就認定為開放
            if has_register_keyword and not has_closed_keyword:
                print("【檢測結果】已開放登記！準備發送郵件通知...")
                send_email(clean_buttons)
            else:
                print("【檢測結果】目前尚未開放登記。")

        except Exception as e:
            print(f"執行時發生錯誤: {e}")
        finally:
            browser.close()


def send_email(button_info):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("錯誤：未設定發件人信箱或密碼環境變數。")
        return

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "【開放登記通知】貓咪公寓/租賃網頁已開放登記！"

    body = (
        f"您關注的網頁狀態已變更！\n\n"
        f"目前頁面偵測到的按鈕狀態：{button_info}\n\n"
        f"請立即點擊連結前往登記：\n{URL}"
    )
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("通知信件發送成功！")
    except Exception as e:
        print(f"寄信失敗: {e}")


if __name__ == "__main__":
    check_availability()
