from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional

_DEFAULT_LOCATION = "San Francisco, California, United States"


class SearchMetadata(BaseModel):
    id: str
    status: str
    json_endpoint: HttpUrl
    created_at: str
    processed_at: str
    google_url: HttpUrl
    raw_html_file: HttpUrl
    total_time_taken: float


class SearchParameters(BaseModel):
    q: str
    api_key: Optional[str] = None
    engine: str = "google"
    location_requested: str = _DEFAULT_LOCATION
    location_used: str = _DEFAULT_LOCATION
    google_domain: str = "google.com"
    hl: str = "en"
    gl: str = "us"
    num: Optional[str] = None
    device: Optional[str] = None
    start: Optional[str] = None
    safe: Optional[str] = None  # Safe search
    filter: Optional[str] = None  # Duplicate content filter
    tbm: Optional[str] = None  # Search type (images, videos, news, etc.)
    tbs: Optional[str] = None  # Search time range
    lr: Optional[str] = None  # Language restriction
    cr: Optional[str] = None  # Country restriction
    uule: Optional[str] = None  # Encoded location
    cx: Optional[str] = None  # Custom search engine ID
    date_restrict: Optional[str] = None  # Date restriction
    exact_terms: Optional[str] = None  # Exact terms
    exclude_terms: Optional[str] = None  # Exclude terms
    file_type: Optional[str] = None  # File type
    rights: Optional[str] = None  # Usage rights


class KnowledgeGraph(BaseModel):
    title: str
    type: str
    entity_type: str
    kgmid: str
    knowledge_graph_search_link: HttpUrl
    serpapi_knowledge_graph_search_link: HttpUrl
    founded: Optional[str] = None
    number_of_employees: Optional[str] = None
    owner: Optional[str] = None
    owner_links: Optional[List[Dict[str, str]]] = None


class OrganicResult(BaseModel):
    position: int
    title: str
    link: HttpUrl
    redirect_link: HttpUrl
    displayed_link: str
    favicon: HttpUrl
    snippet: str
    snippet_highlighted_words: List[str]
    source: str


class RelatedSearch(BaseModel):
    block_position: int
    query: str
    link: HttpUrl
    serpapi_link: HttpUrl


class Pagination(BaseModel):
    current: int
    next: Optional[HttpUrl]
    other_pages: Dict[str, HttpUrl]


class SerpapiPagination(BaseModel):
    current: int
    next_link: Optional[HttpUrl]
    next: Optional[HttpUrl]
    other_pages: Dict[str, HttpUrl]


class SearchInformation(BaseModel):
    query_displayed: str
    total_results: int | None = str
    time_taken_displayed: float | None = None
    organic_results_state: str


class SearchResult(BaseModel):
    search_metadata: SearchMetadata
    search_parameters: SearchParameters
    search_information: SearchInformation
    knowledge_graph: Optional[KnowledgeGraph] = None
    organic_results: List[OrganicResult]
    related_searches: List[RelatedSearch]
    pagination: Pagination
    serpapi_pagination: SerpapiPagination
