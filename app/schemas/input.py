from enum import Enum
from pydantic import BaseModel, HttpUrl
from typing import Optional, Union

class ResourceType(str, Enum):
    FILE = "file"
    YOUTUBE = "youtube"
    WEB = "web"

class BaseResourceInput(BaseModel):
    resource_type: ResourceType

class PDFResourceInput(BaseResourceInput):
    resource_type: ResourceType = ResourceType.FILE
    file_url: str

class URLResourceInput(BaseResourceInput):
    resource_type: ResourceType
    url: HttpUrl

class GenerateRequest(BaseModel):
    resource_type: ResourceType
    resource_data: Union[str, HttpUrl]
    collection_id: str 