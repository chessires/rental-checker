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
        # 啟動無頭瀏覽器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("正在載入網頁...")
            page.goto(URL, wait_until="networkidle", timeout=30000)
            
            # 等待頁面文字載入完畢（可根據狀況稍作緩衝）
            page.wait_for_timeout(3000)

            # 抓取瀏覽器渲染後的完整頁面內容
            content = page.content()
            page_text = page.inner_text("body")

            print("--- 網頁載入完成，開始比對狀態 ---")

            # 只要頁面出現「立即登記」，且不再顯示「非開放登記時間」
            if "立即登記" in page_text and "非開放登記時間" not in page_text:
                print("【檢測結果】已開放登記！準備發送郵件通知...")
                send_email()
            else:
                print("【檢測結果】目前尚未開放登記。")

        except Exception as e:
            print(f"執行時發生錯誤: {e}")
        finally:
            browser.close()


def send_email():
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("錯誤：未設定發件人信箱或密碼環境變數。")
        return

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "【開放登記通知】網頁已開放登記！"

    body = f"您關注的網頁已變更狀態為【立即登記】！\n\n請立即點擊連結前往登記：\n{URL}"
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
