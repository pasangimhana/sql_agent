# SQL Agent System

A modular agent-based system for processing SQL queries and generating natural language reports using AutoGen.

## Overview

This system provides an intelligent interface for interacting with SQL databases through natural language. It uses a multi-agent architecture built with AutoGen to parse user queries, generate and execute SQL, and create comprehensive reports.

## Architecture

The system consists of five specialized agents working in concert:

1. **Orchestrator Agent**: 
   - Central control hub that manages the workflow
   - Coordinates communication between agents
   - Handles error recovery and retries
   - Compiles and delivers final reports

2. **Query Parser Agent**: 
   - Analyzes natural language queries
   - Generates optimized SQL statements
   - Validates SQL syntax and structure
   - Refines queries based on execution feedback

3. **Executor Agent**: 
   - Manages database connections
   - Executes SQL queries safely
   - Provides immediate feedback on query execution
   - Reports errors and execution results

4. **Report Generator Agent**: 
   - Processes query results
   - Creates natural language reports
   - Formats output for readability
   - Ensures reports are fact-based and concise

5. **Schema Provider Agent**:
   - Extracts and processes database schema
   - Provides structured schema information
   - Ensures data integrity
   - Prevents schema hallucinations

## Project Structure

```
modular-agents/
├── agents.py           # Agent implementations
├── main.py            # Main entry point and system initialization
├── tools.py           # Utility functions for database operations
├── state.py           # State management
├── requirements.txt   # Project dependencies
└── readme.md         # This file
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create a .env file with:
OPENAI_API_KEY=your_api_key
DB_PATH=path_to_your_database
```

## Running the System

### Method 1: Direct Execution

Run the main script directly:
```bash
python main.py
```
This will execute the default query: "What were the sales last 2 month?"

### Method 2: Interactive Usage

Create a Python script (e.g., `run_query.py`) with your custom query:
```python
from main import main

# Initialize the system
manager = main()

# Process your custom query
chat = manager.initiate_chat(
    manager.groupchat.agents[0],  # The orchestrator agent
    message="Your custom query here"  # Replace with your query
)
print(chat.summary())
```

Then run your script:
```bash
python run_query.py
```

### Method 3: Import as Module

Import and use the system in your own code:
```python
from main import main

def process_query(query: str):
    manager = main()
    chat = manager.initiate_chat(
        manager.groupchat.agents[0],
        message=query
    )
    return chat.summary()

# Example usage
result = process_query("Show me the top 10 customers by revenue")
print(result)
```

## Dependencies

- `pyautogen>=0.2.0`: For agent orchestration and communication
- `openai>=1.0.0`: For language model integration
- `python-dotenv>=1.0.0`: For environment variable management
- `db-sqlite3`: For database operations

## Features

- Natural language to SQL conversion
- Intelligent query optimization
- Comprehensive error handling
- Transaction management
- Report generation with insights
- Configurable agent behavior
- Extensible architecture
- Schema-aware query generation
- Multi-agent collaboration

## Error Handling

The system includes comprehensive error handling:
- SQL syntax errors are caught and reported
- Database connection issues are handled gracefully
- Query execution errors are logged and reported
- The system can retry failed operations when appropriate
- Detailed error messages for debugging
- Schema validation and integrity checks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
