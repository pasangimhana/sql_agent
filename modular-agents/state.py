from typing import Dict, Any, Optional
from pydantic import BaseModel

class QueryState(BaseModel):
    """State for tracking query processing."""
    user_query: str
    sql_queries: list[str] = []
    query_results: list[Dict[str, Any]] = []
    error_messages: list[str] = []
    final_report: Optional[str] = None
