import sqlite3
from typing import Dict, Any

def query_executor(query: str, db_path: str) -> Dict[str, Any]:
    """Executes SQL queries against the database and returns results.
    
    Args:
        query (str): The SQL query to execute
        db_path (str): Path to the SQLite database file
        
    Returns:
        Dict[str, Any]: Query results with columns and data, or error information
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            return {
                "success": True,
                "columns": columns,
                "results": results
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def schema_provider(db_path: str) -> Dict[str, Any]:
    """Extracts and provides the database schema information.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        Dict[str, Any]: Database schema information or error details
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema_info = {}
            for table in tables:
                table_name = table[0]
                # Get table structure
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                # Get foreign key information
                cursor.execute(f"PRAGMA foreign_key_list({table_name});")
                foreign_keys = cursor.fetchall()
                
                schema_info[table_name] = {
                    "columns": columns,
                    "foreign_keys": foreign_keys
                }
            
            return {
                "success": True,
                "schema": schema_info
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
