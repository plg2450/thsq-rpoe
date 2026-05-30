import os
import re
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from config import DATA_DIR


class Downloader:
    def __init__(self):
        self.output_dir = os.path.join(DATA_DIR, "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_url(self, text: str) -> str:
        patterns = [
            r'https?://v\.douyin\.com/\S+',
            r'https?://www\.douyin\.com/\S+',
            r'https?://www\.iesdouyin\.com/\S+',
            r'https?://v\.ixigua\.com/\S+',
            r'https?://www\.ixigua\.com/\S+',
            r'https?://youtu\.be/\S+',
            r'https?://www\.youtube\.com/\S+',
            r'https?://\S+',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).rstrip('/')
        return text.strip()

    def download_audio(self, url: str) -> str:
        url = self.extract_url(url)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            stealth = Stealth()
            stealth.apply_stealth_sync(page)

            media_urls = []

            def handle_response(response):
                try:
                    ct = response.headers.get("content-type", "")
                    if "video" in ct or "audio" in ct:
                        cl = response.headers.get("content-length", "0")
                        media_urls.append({
                            "url": response.url,
                            "type": ct,
                            "size": int(cl) if cl.isdigit() else 0
                        })
                except:
                    pass

            page.on("response", handle_response)

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)

            page_url = page.url
            video_id_match = re.search(r'/video/(\d+)', page_url)
            if not video_id_match:
                page.wait_for_timeout(3000)
                video_id_match = re.search(r'/video/(\d+)', page.url)

            if not video_id_match:
                browser.close()
                raise ValueError("无法获取视频ID")

            video_id = video_id_match.group(1)

            # 检查是否已下载过
            output_path = os.path.join(self.output_dir, f"{video_id}.mp4")
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                browser.close()
                return output_path

            html = page.content()
            cookies = context.cookies()
            browser.close()

        audio_url = None

        patterns_to_try = [
            r'"playAddr".*?"url_list":\s*\["(https?://[^"]+)"',
            r'"play_addr".*?"url_list":\s*\["(https?://[^"]+)"',
            r'"src":\s*"(https?://[^"]*\.(mp4|mp3|m3u8)[^"]*)"',
            r'video_url["\s:=]+["\']?(https?://[^"\'<>\s]+)',
            r'"url":\s*"(https?://v[^"]*)"',
        ]

        for pattern in patterns_to_try:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                audio_url = match.group(1)
                break

        if not audio_url and media_urls:
            largest = max(media_urls, key=lambda x: x["size"])
            audio_url = largest["url"]

        if not audio_url:
            match = re.search(r'"video":\s*\{[^}]*"playApi":\s*"([^"]+)"', html)
            if match:
                api_path = match.group(1)
                if api_path.startswith("/"):
                    audio_url = f"https://www.douyin.com{api_path}"
                else:
                    audio_url = api_path

        if not audio_url:
            raise ValueError("无法获取视频地址，请确保视频链接有效")

        output_path = os.path.join(self.output_dir, f"{video_id}.mp4")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/",
        }
        resp = requests.get(audio_url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
            raise FileNotFoundError("文件下载失败")

        return output_path


if __name__ == "__main__":
    dl = Downloader()
    url = input("请输入抖音分享链接: ")
    path = dl.download_audio(url)
    print(f"下载完成: {path}")
