# 🎙️ Auto Podcast Generator  
**Turn any YouTube video, PDF, or web page into a ready-to-listen podcast script in seconds**

> *Lightning-fast, zero-jargon automation for creators, marketers & educators.*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org) 
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Why you’ll love it 🚀
- **One-click automation** – drop a link or file, get a polished, dialogue-style script ready for TTS or recording.  
- **Human-sounding conversations** – powered by [Wetrocloud](https://wetrocloud.com/) ✦ smart AI that writes natural back-and-forth between two hosts.  
- **Works everywhere** – YouTube, PDFs, blogs, research papers, landing pages… anything with words.  
- **Zero setup fuss** – no background audio tools to learn; the app creates, stores & (optionally) hosts your finished audio.  
- **Built for growth** – keyword-rich transcripts boost SEO & accessibility for your podcast episodes.

---

## ✨ Feature Cheat-Sheet
| Task | What happens |
|------|--------------|
| **Paste a URL / upload a file** | Automatically stored in a Wetrocloud collection |
| **Hit “Generate”** | App writes a show outline, intro/outro & host dialogue |
| **Need audio?** | Built-in Podcastfy engine voices your script & uploads to S3 |
| **Get the link** | Share your MP3 or edit further in your favourite DAW |

---

## 🚀 Quick Start

```bash
# 1. Clone & enter the project
git clone https://github.com/yourname/auto-podcast-generator.git
cd auto-podcast-generator

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file and add your API keys
WETRO_API_KEY=your_wetrocloud_key
OPENAI_API_KEY=optional
GEMINI_API_KEY=optional
```

---

## ▶️ Usage Overview

You can integrate the transcript and audio generation into your pipeline, using the provided services:

1. **WetrocloudService**: Ingests a resource and generates a podcast-style transcript
2. **PodcastfyService**: Converts transcript text into audio using a local or external TTS engine
3. **FileUploadService**: Uploads files to a public endpoint and returns a URL

Each module is modular and can be used individually or combined in a custom flow.

---

## 🧱 Example Workflow (Conceptual)

```text
YouTube URL / PDF / webpage
        ↓
WetrocloudService.generate_transcript()
        ↓
Transcript saved to file
        ↓
PodcastfyService.generate_audio()
        ↓
Audio file uploaded via FileUploadService
        ↓
URL to audio returned (usable in any RSS feed or player)
```

**Note:** This repo does not auto-publish podcasts, but the outputs (transcript + audio URL) can easily be integrated into publishing platforms, podcast feeds, or voice pipelines.

---

## 🔐 Environment Variables

Create a `.env` file in your root directory with the following:

```
WETRO_API_KEY=your_wetrocloud_key
OPENAI_API_KEY=your_openai_key_if_using_tts
GEMINI_API_KEY=your_gemini_key_if_using_tts
```

---

## ✅ Requirements

- Python 3.9+
- `wetro`, `httpx`, `fastapi`, and other dependencies in `requirements.txt`
- API key from [Wetrocloud](https://wetrocloud.com/)

---

## 📦 Outputs

- `podcast_transcript.txt`: a well-structured, speaker-formatted text transcript
- (optional) `*.mp3` or `*.wav`: generated audio file
- (optional) Shareable audio URL after upload

These outputs can be fed into TTS platforms, podcast hosting tools, or used directly in educational/audio workflows.

---

## 🪪 License

MIT License.... free for personal and commercial use.

---

## 🙋‍♀️ Who’s This For?

If you’re searching for:
- *“how to convert YouTube video to podcast script”*
- *“generate podcast from PDF”*
- *“AI podcast dialogue generator”*
- *“automated voice-based podcast pipeline”*

…this tool helps kickstart that workflow.

---

## ✨ Powered By

- [Wetrocloud](https://wetrocloud.com/) – AI content extraction and transformation
- OpenAI/Gemini (optional) – for speech synthesis
