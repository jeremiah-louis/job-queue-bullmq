# Podcast Transcript Generator

A Python application that generates podcast-style transcripts from YouTube videos using the Wetrocloud API. The application creates engaging, conversational transcripts with multiple speakers.

## Features

- Converts YouTube videos into podcast-style transcripts
- Uses a structured XML schema for consistent formatting
- Generates natural, conversational dialogue between speakers
- Saves transcripts to text files
- Performance tracking with execution time measurements

## Requirements

- Python 3.x
- wetro package
- python-decouple package

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Set up your Wetrocloud API key in a `.env` file:
```
WETRO_API_KEY=your_api_key_here
```

2. Run the script:
```bash
python transcript-wetro.py
```

The script will:
- Create a collection
- Process the YouTube video
- Generate a transcript
- Save the output to `podcast_transcript.txt`

## Project Structure

- `transcript-wetro.py` - Main script for generating transcripts
- `podcast_transcript.txt` - Output file containing the generated transcript
- `.env` - Configuration file for API keys
- `requirements.txt` - Project dependencies

## License

MIT License 