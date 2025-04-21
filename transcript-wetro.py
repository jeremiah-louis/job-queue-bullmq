from wetro import Wetrocloud
from decouple import config
from time import perf_counter
import os

# Set environment variables
os.environ["WETRO_API_KEY"] = config("WETRO_API_KEY")

# Initialize client
client = Wetrocloud(api_key=config("WETRO_API_KEY"))

# Start timer
start_time = perf_counter()

# Create collection and insert resource
client.collection.create_collection("bootoshi")
client.collection.insert_resource(
    collection_id="bootoshi",
    resource="https://www.youtube.com/watch?v=WMPUyI1YG2g",
    type="youtube",
)

# Generate podcast
json_schema = ["""<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>
<Person2>[Speaker 2's dialogue here]</Person2>
<Person1>[Speaker 1's dialogue here]</Person1>"""]

# Query collection
query = client.collection.query_collection(
    collection_id="bootoshi",
    request_query="Generate a comprehensive podcast episode from the resource provided",
    json_schema=json_schema,
    json_schema_rules="Add opening remarks, replace the text with the information from the resource provided. Emulate a real conversation between two people. Add closing remarks.",
)

# Convert list response to string and write to file
response_text = '\n'.join(query.response) if isinstance(query.response, list) else query.response
with open('podcast_transcript.txt', 'w', encoding='utf-8') as f:
    f.write(response_text)

print("Transcript has been saved to podcast_transcript.txt")

# Print time taken
end_time = perf_counter()
print(f"Time taken: {end_time - start_time} seconds")
