# SQL Agent System

A modular agent-based system for processing SQL queries and generating natural language reports using LangGraph.

## Architecture

The system consists of four main agents:

1. **Orchestrator Agent**: Central control hub that manages the workflow
2. **Query Parser Agent**: Analyzes user queries and generates SQL
3. **Executor Agent**: Executes SQL queries against the database
4. **Report Generator Agent**: Creates natural language reports from query results

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

## Usage

```python
from lang_graph_agent.main import main

# Initialize the system
process_query = main()

# Process a query
result = process_query("What were the sales trends last month?")
print(result)
```

## How it Works

1. The Orchestrator receives the user query and coordinates the workflow
2. The Query Parser analyzes the query and generates appropriate SQL
3. The Executor runs the SQL queries against the database
4. The Report Generator creates a natural language report from the results
5. The final report is returned to the user

## Error Handling

The system includes comprehensive error handling:
- SQL syntax errors are caught and reported
- Database connection issues are handled gracefully
- Query execution errors are logged and reported
- The system can retry failed operations when appropriate

## Contributing

Feel free to submit issues and enhancement requests!
