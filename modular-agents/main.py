import os
from dotenv import load_dotenv
import autogen
import sqlite3
from agents import (
    create_orchestrator_agent,
    create_query_parser_agent,
    create_executor_agent,
    create_report_generator_agent,
    create_schema_provider_agent
)
from tools import query_executor, schema_provider

def check_db_connection(db_path: str) -> bool:
    """Check if the database exists and is accessible.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        with sqlite3.connect(db_path) as conn:
            # Try to execute a simple query to verify connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print(f"Successfully connected to database at {db_path}")
            return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    # Get database path from environment or use default
    db_path = os.getenv("DB_PATH", "analytics.db")
    
    # Check database connection before proceeding
    if not check_db_connection(db_path):
        raise Exception(f"Failed to connect to database at {db_path}. Please check the database path and permissions.")
    
    # Create Autogen config
    autogen_config = [
        {
            "model": "gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    ]
    
    # Create function map for tools
    function_map = {
        "query_executor": lambda query: query_executor(query, db_path),
        "schema_provider": lambda: schema_provider(db_path)
    }
    
    # Create agents with function calling
    orchestrator = create_orchestrator_agent(autogen_config)
    schema_provider_agent = create_schema_provider_agent(autogen_config)
    query_parser = create_query_parser_agent(autogen_config)
    executor = create_executor_agent(autogen_config)
    report_generator = create_report_generator_agent(autogen_config)
    
    # Register functions with agents
    for agent in [orchestrator, schema_provider_agent, query_parser, executor, report_generator]:
        agent.register_function(function_map)
    
    # Create group chat
    groupchat = autogen.GroupChat(
        agents=[orchestrator, schema_provider_agent, query_parser, executor, report_generator],
        messages=[],
        max_round=10
    )
    
    # Create manager with LLM config
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={"config_list": autogen_config}
    )
    
    return manager

if __name__ == "__main__":
    # Initialize the system
    manager = main()
    
    # Process a queryclear
    chat = manager.initiate_chat(
        manager.groupchat.agents[0],  # The orchestrator agent
        message="What were the sales last 2 month?"
    )
    print(chat.summary())
