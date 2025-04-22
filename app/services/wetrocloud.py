from wetro import Wetrocloud
from typing import List, Optional
from uuid import uuid4
import os

class WetrocloudService:
    def __init__(self):
        # Set environment variables
        os.environ["WETRO_API_KEY"] = os.getenv("WETRO_API_KEY")
        self.client = Wetrocloud(api_key=os.getenv("WETRO_API_KEY"))
        
        # Default schema and rules
        self.default_schema = ["""<Person1>[Speaker 1's dialogue here]</Person1>
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
        
        self.default_rules = "Add opening remarks, replace the text with the information from the resource provided. Emulate a real conversation between two people. Add closing remarks."

    async def generate_transcript(
        self,
        collection_id: str,
        resource_url: str,
        resource_type: str,
        json_schema: Optional[List[str]] = None,
        json_schema_rules: Optional[str] = None
    ) -> str:
        """
        Generate a transcript from the given resource using Wetrocloud.
        
        Args:
            collection_id: ID for the collection
            resource_url: URL of the resource (S3 URL for PDFs, YouTube/website URL)
            resource_type: Type of resource (pdf, youtube, website)
            json_schema: Optional custom schema for transcript format
            json_schema_rules: Optional custom rules for transcript generation
            
        Returns:
            Generated transcript as string
        """
        try:
            # Create collection if it doesn't exist
            self.client.collection.create_collection(collection_id)
            
            # Insert resource into collection
            self.client.collection.insert_resource(
                collection_id=collection_id,
                resource=resource_url,
                type=resource_type
            )
            
            # Use provided schema/rules or defaults
            schema = json_schema or self.default_schema
            rules = json_schema_rules or self.default_rules
            
            # Query collection to generate transcript
            query = self.client.collection.query_collection(
                collection_id=collection_id,
                request_query="Generate a comprehensive podcast episode from the resource provided",
                json_schema=schema,
                json_schema_rules=rules
            )
            
            # Convert response to string
            response_text = '\n'.join(query.response) if isinstance(query.response, list) else query.response
            return response_text
            
        except Exception as e:
            raise Exception(f"Failed to generate transcript: {str(e)}") 