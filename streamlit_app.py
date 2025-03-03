import json
import os
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen
from typing import Optional, List

import streamlit as st

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    st.error("`youtube_transcript_api` not installed. Please install using `pip install youtube_transcript_api`")
    st.stop()


# همان کلاس ابزارهای یوتیوب بدون تغییر در منطق کارکرد
class YouTubeTools:
    @staticmethod
    def get_youtube_video_id(url: str) -> Optional[str]:
        """استخراج شناسه ویدیو از یک URL یوتیوب"""
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if hostname == "youtu.be":
            return parsed_url.path[1:]
        if hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                query_params = parse_qs(parsed_url.query)
                return query_params.get("v", [None])[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        return None

    @staticmethod
    def get_video_data(url: str) -> dict:
        """دریافت اطلاعات ویدیو از یک URL یوتیوب"""
        if not url:
            raise ValueError("No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
        except Exception:
            raise ValueError("Error getting video ID from URL")

        try:
            params = {"format": "json", "url": f"https://www.youtube.com/watch?v={video_id}"}
            oembed_url = "https://www.youtube.com/oembed"
            query_string = urlencode(params)
            full_url = oembed_url + "?" + query_string

            with urlopen(full_url) as response:
                response_text = response.read()
                video_data = json.loads(response_text.decode())
                clean_data = {
                    "title": video_data.get("title"),
                    "author_name": video_data.get("author_name"),
                    "author_url": video_data.get("author_url"),
                    "type": video_data.get("type"),
                    "height": video_data.get("height"),
                    "width": video_data.get("width"),
                    "version": video_data.get("version"),
                    "provider_name": video_data.get("provider_name"),
                    "provider_url": video_data.get("provider_url"),
                    "thumbnail_url": video_data.get("thumbnail_url"),
                }
                return clean_data
        except Exception as e:
            raise Exception(f"Error getting video data: {str(e)}")

    @staticmethod
    def get_video_captions(url: str, languages: Optional[List[str]] = None) -> str:
        """دریافت زیرنویس‌های ویدیو از یوتیوب"""
        if not url:
            raise ValueError("No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
        except Exception:
            raise ValueError("Error getting video ID from URL")

        try:
            if languages:
                captions = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            else:
                captions = YouTubeTranscriptApi.get_transcript(video_id)

            if captions:
                return " ".join(line["text"] for line in captions)
            return "No captions found for video"
        except Exception as e:
            raise Exception(f"Error getting captions for video: {str(e)}")

    @staticmethod
    def get_video_timestamps(url: str, languages: Optional[List[str]] = None) -> List[str]:
        """تولید زمان‌بندی بر اساس زیرنویس‌های ویدیو"""
        if not url:
            raise ValueError("No URL provided")

        try:
            video_id = YouTubeTools.get_youtube_video_id(url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
        except Exception:
            raise ValueError("Error getting video ID from URL")

        try:
            captions = YouTubeTranscriptApi.get_transcript(video_id, languages=languages or ["en"])
            timestamps = []
            for line in captions:
                start = int(line["start"])
                minutes, seconds = divmod(start, 60)
                timestamps.append(f"{minutes}:{seconds:02d} - {line['text']}")
            return timestamps
        except Exception as e:
            raise Exception(f"Error generating timestamps: {str(e)}")


# رابط کاربری استریملیت
st.title("YouTube Tools App")
st.write("این اپلیکیشن امکان دریافت اطلاعات متا، زیرنویس‌ها و زمان‌بندی‌های یک ویدیو در یوتیوب را فراهم می‌کند.")

# ورودی URL
url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
# ورودی زبان‌ها (به صورت جدا شده با کاما)
langs_input = st.text_input("زبان‌ها (اختیاری، جدا شده با کاما)", placeholder="en,fa")

# پردازش زبان‌ها به لیست
languages = [lang.strip() for lang in langs_input.split(",") if lang.strip()] if langs_input else None

# استفاده از تب‌ها برای نمایش عملکردها
tab1, tab2, tab3 = st.tabs(["Video Data", "Video Captions", "Video Timestamps"])

with tab1:
    st.header("اطلاعات ویدیو")
    if st.button("دریافت اطلاعات ویدیو", key="video_data"):
        if not url:
            st.error("لطفاً URL ویدیو را وارد کنید")
        else:
            try:
                video_data = YouTubeTools.get_video_data(url)
                st.json(video_data)
            except Exception as e:
                st.error(str(e))

with tab2:
    st.header("زیرنویس‌های ویدیو")
    if st.button("دریافت زیرنویس‌ها", key="video_captions"):
        if not url:
            st.error("لطفاً URL ویدیو را وارد کنید")
        else:
            try:
                captions = YouTubeTools.get_video_captions(url, languages)
                st.text_area("متن زیرنویس‌ها", captions, height=300)

                st.text_area("ترجمه", captions, height=300)

            except Exception as e:
                st.error(str(e))

with tab3:
    st.header("زمان‌بندی‌های ویدیو")
    if st.button("دریافت زمان‌بندی‌ها", key="video_timestamps"):
        if not url:
            st.error("لطفاً URL ویدیو را وارد کنید")
        else:
            try:
                timestamps = YouTubeTools.get_video_timestamps(url, languages)
                st.write("\n".join(timestamps))
            except Exception as e:
                st.error(str(e))
