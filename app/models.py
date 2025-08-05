from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ResourceType(str, Enum):
    """Enumeration of web resource types"""

    JSON = "json"
    JAVASCRIPT = "js"
    XML = "xml"
    YAML = "yml"
    CSS = "css"
    IMAGE = "image"
    HTML = "html"
    TEXT = "txt"
    PDF = "pdf"
    OTHER = "other"


class ScanStatus(str, Enum):
    """Status of URL scanning process"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Persistent models (stored in database)


class ScanSession(SQLModel, table=True):
    """Represents a URL scanning session with authentication details"""

    __tablename__ = "scan_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    target_url: str = Field(max_length=2048, index=True)
    status: ScanStatus = Field(default=ScanStatus.PENDING)

    # Authentication fields
    username: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=255)  # Should be encrypted in production
    auth_token: Optional[str] = Field(default=None, max_length=1024)

    # Optional payload for admin requests
    payload: Optional[str] = Field(default=None, max_length=10000)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Statistics
    total_resources_found: int = Field(default=0)
    scan_duration_seconds: Optional[float] = Field(default=None)

    # Relationships
    resources: List["WebResource"] = Relationship(back_populates="scan_session")


class WebResource(SQLModel, table=True):
    """Represents a discovered web resource"""

    __tablename__ = "web_resources"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    scan_session_id: int = Field(foreign_key="scan_sessions.id", index=True)

    # Resource details
    url: str = Field(max_length=2048)
    relative_path: str = Field(max_length=1024)
    resource_type: ResourceType = Field(index=True)
    file_extension: str = Field(max_length=10, index=True)

    # Resource metadata
    content_type: Optional[str] = Field(default=None, max_length=100)
    file_size_bytes: Optional[int] = Field(default=None)
    last_modified: Optional[datetime] = Field(default=None)

    # Download status
    is_downloadable: bool = Field(default=True)
    download_attempts: int = Field(default=0)
    last_download_at: Optional[datetime] = Field(default=None)

    # Discovery metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    source_element: Optional[str] = Field(default=None, max_length=50)  # e.g., 'img', 'script', 'link'

    # Relationships
    scan_session: ScanSession = Relationship(back_populates="resources")


class DownloadHistory(SQLModel, table=True):
    """Track resource download history"""

    __tablename__ = "download_history"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    resource_id: int = Field(foreign_key="web_resources.id", index=True)

    # Download details
    downloaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: Optional[int] = Field(default=None)
    download_duration_seconds: Optional[float] = Field(default=None)

    # Status and error tracking
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None, max_length=500)

    # Client information
    client_ip: Optional[str] = Field(default=None, max_length=45)  # IPv6 compatible
    user_agent: Optional[str] = Field(default=None, max_length=500)


# Non-persistent schemas (for validation, forms, API requests/responses)


class ScanRequest(SQLModel, table=False):
    """Schema for initiating a new URL scan"""

    target_url: str = Field(max_length=2048, regex=r"^https?://[^\s/$.?#].[^\s]*$")
    username: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=255)
    auth_token: Optional[str] = Field(default=None, max_length=1024)
    payload: Optional[str] = Field(default=None, max_length=10000)


class ScanResponse(SQLModel, table=False):
    """Schema for scan session response"""

    id: int
    target_url: str
    status: ScanStatus
    created_at: str  # ISO format datetime
    total_resources_found: int
    error_message: Optional[str] = None


class ResourceResponse(SQLModel, table=False):
    """Schema for web resource response"""

    id: int
    url: str
    relative_path: str
    resource_type: ResourceType
    file_extension: str
    content_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    last_modified: Optional[str] = None  # ISO format datetime
    is_downloadable: bool
    discovered_at: str  # ISO format datetime
    source_element: Optional[str] = None


class ResourceListResponse(SQLModel, table=False):
    """Schema for paginated resource list"""

    resources: List[ResourceResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class DownloadRequest(SQLModel, table=False):
    """Schema for resource download request"""

    resource_id: int
    client_ip: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)


class ScanStatusUpdate(SQLModel, table=False):
    """Schema for updating scan status"""

    status: ScanStatus
    error_message: Optional[str] = Field(default=None, max_length=1000)
    total_resources_found: Optional[int] = Field(default=None)
    scan_duration_seconds: Optional[float] = Field(default=None)


class ResourceFilter(SQLModel, table=False):
    """Schema for filtering resources"""

    resource_types: Optional[List[ResourceType]] = Field(default=None)
    file_extensions: Optional[List[str]] = Field(default=None)
    min_file_size: Optional[int] = Field(default=None)
    max_file_size: Optional[int] = Field(default=None)
    is_downloadable: Optional[bool] = Field(default=None)
    search_query: Optional[str] = Field(default=None, max_length=255)
