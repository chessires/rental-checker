import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# 監控目標網址與通知信箱
URL = "https://rental.aconeco.com/21"
TO_EMAIL = "chessires@gmail.com"

# 發信設定（從 GitHub Secrets 讀取）
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")


def check_availability():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()

        # 解析網頁內容
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        # 判斷條件：出現「立即登記」且不再出現「非開放登記時間」
        if "立即登記" in page_text and "非開放登記時間" not in page_text:
            print("【檢測結果】已開放登記！準備發送郵件通知...")
            send_email()
        else:
            print("【檢測結果】目前尚未開放登記（狀態未變更）。")

    except Exception as e:
        print(f"爬取網頁時發生錯誤: {e}")


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
