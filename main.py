from podcastfy.client import generate_podcast
from decouple import config
from time import perf_counter
import os

# Set environment variables
os.environ["GEMINI_API_KEY"] = config("GEMINI_API_KEY")
os.environ["OPENAI_API_KEY"] = config("OPENAI_API_KEY")

# Generate podcast
start_time = perf_counter()
audio_file = generate_podcast(transcript_file="podcast_transcript.txt")

# Print time taken
end_time = perf_counter()
print(f"Time taken: {end_time - start_time} seconds")