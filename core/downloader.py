import os
import re
import json
import subprocess
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from config import DATA_DIR, FFMPEG_PATH


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

            # 收集所有网络请求的视频URL
            all_video_urls = []

            def handle_response(response):
                try:
                    ct = response.headers.get("content-type", "")
                    url_str = response.url
                    # 只收集可能是视频的URL
                    if any(ext in url_str.lower() for ext in ['.mp4', 'video', 'play']):
                        cl = response.headers.get("content-length", "0")
                        size = int(cl) if cl.isdigit() else 0
                        all_video_urls.append({
                            "url": url_str,
                            "type": ct,
                            "size": size
                        })
                except:
                    pass

            page.on("response", handle_response)

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(10000)

            page_url = page.url
            video_id_match = re.search(r'/video/(\d+)', page_url)
            if not video_id_match:
                page.wait_for_timeout(3000)
                video_id_match = re.search(r'/video/(\d+)', page.url)

            if not video_id_match:
                browser.close()
                raise ValueError("无法获取视频ID，请确保链接是抖音视频分享链接")

            video_id = video_id_match.group(1)

            # 检查是否已下载过
            output_path = os.path.join(self.output_dir, f"{video_id}.mp4")
            if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                if self._has_audio_stream(output_path):
                    browser.close()
                    return output_path

            # 从页面JSON数据中提取视频信息
            html = page.content()
            browser.close()

        # 方法1: 从页面JSON数据提取完整视频URL
        video_url = self._extract_from_json(html, video_id)

        # 方法2: 从网络请求中找大文件（通常是完整视频）
        if not video_url and all_video_urls:
            # 过滤掉小文件（预览/缩略图），只保留>1MB的
            large_videos = [v for v in all_video_urls if v["size"] > 1000000]
            if large_videos:
                video_url = max(large_videos, key=lambda x: x["size"])["url"]

        # 方法3: 正则匹配
        if not video_url:
            video_url = self._extract_from_regex(html)

        if not video_url:
            raise ValueError("无法获取视频地址，请确保视频链接有效且不是私密视频")

        # 下载视频
        self._download_file(video_url, output_path)

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 10000:
            raise FileNotFoundError("文件下载失败，请重试")

        # 检查音频轨道
        if not self._has_audio_stream(output_path):
            os.remove(output_path)
            raise ValueError("下载的视频没有音频轨道，可能是直播回放或纯视频，请换一个视频试试")

        return output_path

    def _extract_from_json(self, html: str, video_id: str) -> str:
        """从页面JSON数据中提取视频URL"""
        # 尝试多种JSON模式
        patterns = [
            # 模式1: playAddr
            r'"playApi"\s*:\s*"([^"]+)"',
            r'"play_addr".*?"url_list"\s*:\s*\["([^"]+)"',
            r'"playAddr".*?"url_list"\s*:\s*\["([^"]+)"',
            # 模式2: video URL
            r'"video_url"\s*:\s*"([^"]+)"',
            r'"url"\s*:\s*"(https?://[^"]*video[^"]*)"',
            # 模式3: src属性
            r'"src"\s*:\s*"(https?://[^"]*\.(mp4|m3u8)[^"]*)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                url = match.group(1)
                # 处理相对路径
                if url.startswith("//"):
                    url = "https:" + url
                elif url.startswith("/"):
                    url = "https://www.douyin.com" + url
                return url

        return None

    def _extract_from_regex(self, html: str) -> str:
        """正则匹配视频URL"""
        patterns = [
            r'"url":\s*"(https?://v[^"]*)"',
            r'video_url["\s:=]+["\']?(https?://[^"\'<>\s]+)',
            r'(https?://[^"\'<>\s]*\.mp4[^"\'<>\s]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _download_file(self, url: str, output_path: str):
        """下载文件"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/",
        }
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        resp.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

    def _has_audio_stream(self, video_path: str) -> bool:
        """检查视频是否包含音频轨道"""
        cmd = [
            FFMPEG_PATH,
            "-i", video_path,
            "-f", "null",
            "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "Audio:" in result.stderr


if __name__ == "__main__":
    dl = Downloader()
    url = input("请输入抖音分享链接: ")
    path = dl.download_audio(url)
    print(f"下载完成: {path}")
