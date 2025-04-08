import asyncio
from datetime import datetime
import logging
import markdown
import os
from os import path
import re
import sqlite3
import traceback
from typing import Any, List, Optional
from typing_extensions import Annotated

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv, find_dotenv
import pandas as pd
import plotly.express as px
import plotly.io as pio


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    cyan = "\x1b[36;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: cyan + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

load_dotenv(find_dotenv())

DB_PATH = f"{path.dirname(__file__)}/../analytics.db"


RESPONSE_STATE = {
    "data": [],
    "plot": [],
    "aggregate": [],
    "markdown": [],
}


def execute_query(query: Annotated[str, "SQL query to execute"]) -> List[dict]:
    """Execute SQL query and return results as a list of dictionaries"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        conn.close()
        # Convert data to list of dictionaries
        results = [{columns[i]: row[i] for i in range(len(columns))} for row in data]
        # logger.debug(f"Executed query: {query}")
        # logger.debug(f"Results: {results}")
        # logger.debug("\n\n")
        return results
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise ValueError(f"Error executing query: {e}")


execute_query_tool = FunctionTool(
    execute_query,
    name="execute_query",
    description="Execute SQL query on the SQLite database",
)


def calculate_aggregate(col: str, aggregate_func: str) -> Any:
    """Calculate aggregate values (sum, average, etc.) for a given list of data"""
    rows = RESPONSE_STATE["data"][-1]
    try:
        aggregate_func = aggregate_func.lower()
        if aggregate_func == "sum":
            return sum(item[col] for item in rows)
        elif aggregate_func == "average":
            return sum(item[col] for item in rows) / len(rows)
        elif aggregate_func == "min":
            return min(item[col] for item in rows)
        elif aggregate_func == "max":
            return max(item[col] for item in rows)
        elif aggregate_func == "count":
            return len(rows)
        else:
            raise ValueError(f"Unsupported aggregate function: {aggregate_func}")
    except Exception as e:
        logger.error(f"Error calculating aggregate: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Error calculating aggregate: {e}")


calculate_aggregate_tool = FunctionTool(
    calculate_aggregate,
    name="calculate_aggregate",
    description="Calculate aggregate values for a given data series",
)


def create_plot(
    plot_type: str,
    x_key: Optional[str] = None,
    y_key: Optional[str] = None,
    title: str = "Data Visualization",
) -> dict:
    """
    Create different types of plots based on data characteristics using plotly

    Parameters:
    data: List of dictionaries containing the data to plot
    plot_type: Type of plot (bar, line, scatter, pie, area, histogram)
    x_key: Dictionary key to use for x-axis values
    y_key: Dictionary key to use for y-axis values
    title: Title of the plot

    Returns:
    dict: Plotly figure object as JSON-serializable dict
    """
    data = RESPONSE_STATE["data"][-1]
    try:

        # Convert list of dicts to DataFrame for easier plotting
        df = pd.DataFrame(data)

        # If keys aren't specified, use the first two columns
        if x_key is None and len(df.columns) > 0:
            x_key = df.columns[0]

        if y_key is None and len(df.columns) > 1:
            y_key = df.columns[1]

        # Create appropriate plot based on type
        fig = None

        if plot_type.lower() == "bar":
            fig = px.bar(df, x=x_key, y=y_key, title=title)
        elif plot_type.lower() == "line":
            fig = px.line(df, x=x_key, y=y_key, title=title)
        elif plot_type.lower() == "scatter":
            fig = px.scatter(df, x=x_key, y=y_key, title=title)
        elif plot_type.lower() == "pie":
            fig = px.pie(df, values=y_key, names=x_key, title=title)
        elif plot_type.lower() == "area":
            fig = px.area(df, x=x_key, y=y_key, title=title)
        elif plot_type.lower() == "histogram":
            fig = px.histogram(df, x=y_key, title=title)
        elif plot_type.lower() == "heatmap":
            # For heatmap, additional logic might be needed to structure the data properly
            if len(df.columns) >= 3:  # Need at least 3 columns for x, y, and value
                pivot_df = df.pivot(index=x_key, columns=y_key, values=df.columns[2])
                fig = px.imshow(pivot_df, title=title)
            else:
                raise ValueError("Heatmap requires at least 3 columns of data")
        else:
            raise ValueError(f"Unsupported plot type: {plot_type}")

        # Update layout
        fig.update_layout(
            title={
                "text": title,
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            xaxis_title=x_key,
            yaxis_title=y_key,
            template="plotly_white",
        )

        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    except Exception as e:
        logger.error(f"Error creating plot: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Error creating plot: {e}")


# Create function tool instance
create_plot_tool = FunctionTool(
    create_plot,
    name="create_plot",
    description="Create a plotly visualization from a list of dictionaries. Specify x_key and y_key as the dictionary keys to use for plotting.",
)


def create_report_analysis(title: str, sections: list) -> str:
    """
    Generate a markdown report from provided sections

    Parameters:
    title (str): The title of the report
    sections (list): List of dictionaries with structure:
                    {
                      'heading': 'Section Heading',
                      'content': 'Text content...'
                    }

    Returns:
    str: Markdown formatted report
    """
    try:

        # Start with the title and timestamp
        markdown = f"# {title}\n\n"
        markdown += (
            f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        )

        # Add each section
        # plot_counter = 0
        for i, section in enumerate(sections):
            if "heading" in section:
                markdown += f"## {section['heading']}\n\n"

            if "content" in section:
                markdown += f"{section['content']}\n\n"

            if "plot" in section:
                markdown += f"<!-- plot {i} -->\n\n"

        return markdown

    except Exception as e:
        logger.error(f"Error creating report: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Error creating report: {e}")


def write_to_html(output_file: str = "report.html") -> str:
    """
    Convert markdown report to HTML with plotly visualizations and write to file

    Parameters:
    markdown_content (str): Markdown content with plot data in comments
    output_file (str): Path to output HTML file

    Returns:
    str: Path to the created HTML file
    """
    markdown_content = "\n".join(RESPONSE_STATE["markdown"])

    try:

        # HTML template with plotly.js included
        html_template = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Data Analysis Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    line-height: 1.6;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                .plotly-graph {{
                    width: 100%;
                    height: 450px;
                    margin: 20px 0;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }}
                h1 {{ color: #2c3e50; margin-top: 0.5em; }}
                h2 {{ color: #3498db; margin-top: 1em; }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                th, td {{
                    text-align: left;
                    padding: 12px;
                    border-bottom: 1px solid #ddd;
                }}
                th {{ background-color: #f8f8f8; }}
            </style>
        </head>
        <body>
            <div id="report-s1">
            {content}
            </div>
            <br>
            <hr>
            <div id="report-s2">
            {plot_content}
            </div>
        </body>
        </html>
        """

        # Convert markdown to HTML (excluding plot comments)
        html_content = markdown.markdown(
            re.sub(r"<!-- plot \d+ -->", "", markdown_content),
            extensions=["tables"],
        )

        # Extract plot data from comments and create plotting scripts
        plot_contents = RESPONSE_STATE["plot"]
        parsed_plot_contents = []
        for _pid, plot_data in enumerate(plot_contents):
            plot_id = f"plot_{_pid}"
            plot_html = f"""
            <div id='{plot_id}' class='plotly-graph'>{plot_data}</div>
            """
            parsed_plot_contents.append(plot_html)

        # Combine HTML content with plot scripts
        final_html = html_template.format(
            content=html_content, plot_content="\n".join(parsed_plot_contents)
        )

        # Write to file
        file_path = path.join(path.dirname(__file__), output_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        return output_file

    except Exception as e:
        logger.error(f"Error writing to HTML: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Error writing to HTML: {e}")


create_plot_tool = FunctionTool(
    create_plot,
    name="create_plot",
    description="Create a plotly visualization based on data and plot type",
)

create_report_analysis_tool = FunctionTool(
    create_report_analysis,
    name="create_report",
    description="Generate a markdown report with sections containing inferences and describing data",
)

write_to_html_tool = FunctionTool(
    write_to_html,
    name="write_to_html",
    description="Convert markdown report to HTML and add on the interactive visualizations",
)


SYSTEM_MESSAGE = """You are a data analytics dashboard agent capable of:
    - Converting natural language requests into SQL queries and Querying a SQLite database containing sales and marketing data
    - Creating appropriate visualizations using queried data
    - Calculating aggregate values (sum, average, etc.) for data series which can then be used to make inferences regarding data
    - Generating comprehensive reports with insights
    - Writing the report to an HTML file with embedded visualizations

    A Generic Workflow (In Order):
    1. User provides a task description.
    2. You parse the task and identify the required SQL queries.
    3. You execute the SQL queries using the provided database schema.
    4. You create visualizations based on the queried data.
    x. (Feel free to repeat steps 2,3,4 iteratively for multiple visualizations, preferably 2-3 times)
    5. You calculate aggregate values as needed.
    6. You generate a markdown report with sections containing inferences and describing data (do not include the visualizations here, they will be added later).
    7. You write the report to an HTML file (make sure that write_to_html is the last function called).
    9. Terminate the conversation.

    Database schema:
    - sales(id, date, product_id, customer_id, quantity, unit_price, total_price, (FK) product_id, (FK) customer_id)
    - products(id, name, category, subcategory, cost, price)
    - customers(id, name, region, segment, join_date)
    - marketing(id, campaign, start_date, end_date, spend, channel, target_region, target_segment)

    Additional instructions:
    - Use the tools provided. If you need to use a tool, respond with the tool name and its parameters.
    - Do not provide any false information.
    - If the data from the previous response is needed to call a function, make sure to include it in the next response.
    - Avoid where queries with date ranges when using the execute_query tool since the database is small.
    - Make sure that write_to_html is the last function called.
    """


# # Main execution function
# async def main():
#     model_client = OpenAIChatCompletionClient(
#         # model="gemini-2.0-flash",
#         # api_key=os.environ["GEMINI_API_KEY"],
#         model="gpt-4o-mini",
#         api_key=os.environ["OPENAI_API_KEY"],
#         parallel_tool_calls=False,
#     )
#     looped_assistant = AssistantAgent(
#         name="LoopedAssistant",
#         model_client=model_client,
#         system_message=SYSTEM_MESSAGE,
#         tools=[
#             execute_query_tool,
#             create_plot_tool,
#             calculate_aggregate_tool,
#             create_report_tool,
#             write_to_html_tool,
#         ],
#     )
#     termination_condition = TextMessageTermination(
#         "looped_assistant"
#     ) | MaxMessageTermination(max_messages=3)

#     team = RoundRobinGroupChat(
#         [looped_assistant],
#         termination_condition=termination_condition,
#     )

#     async for message in team.run_stream(
#         task="Create a quarterly sales analysis report with visualizations of revenue\
#                                           by product category and recommendations for next quarter."
#     ):
#         if hasattr(message, "to_text"):
#             logger.info(message.to_text())
#             logger.info("\n\n")
#         else:
#             logger.info(message.messages)
#             logger.info("\n\n")

#     await model_client.close()


# Main execution function
async def main():
    global RESPONSE_STATE

    model_client = OpenAIChatCompletionClient(
        # model="gemini-2.0-flash",
        # api_key=os.environ["GEMINI_API_KEY"],
        model="gpt-4o-mini",
        api_key=os.environ["OPENAI_API_KEY"],
        parallel_tool_calls=False,
    )
    looped_assistant = AssistantAgent(
        name="LoopedAssistant",
        model_client=model_client,
        system_message=SYSTEM_MESSAGE,
        tools=[
            execute_query_tool,
            create_plot_tool,
            calculate_aggregate_tool,
            create_report_analysis_tool,
            write_to_html_tool,
        ],
    )

    init_message = [
        TextMessage(
            content="Create a quarterly sales analysis report with visualizations of \
                revenue by product category, any other interesting data visualized and recommendations for next quarter.",
            source="user",
        )
    ]
    counter = 0
    while True:
        response = await looped_assistant.on_messages(
            messages=init_message,
            cancellation_token=CancellationToken(),
        )
        func_name = None
        for _ in response.inner_messages:
            logger.debug(_.content)
            if isinstance(_.content[0], str):
                continue
            logger.info(_.content[0].name)
            func_name = _.content[0].name
        logger.info(response.chat_message.content + "\n\n")
        if response.chat_message.type == "ToolCallSummaryMessage":
            if func_name == "execute_query":
                RESPONSE_STATE["data"].append(eval(response.chat_message.content))
            elif func_name == "create_plot":
                RESPONSE_STATE["plot"].append(response.chat_message.content)
            elif func_name == "calculate_aggregate":
                RESPONSE_STATE["aggregate"].append(
                    eval(response.chat_message.content)
                )
            elif func_name == "create_report":
                RESPONSE_STATE["markdown"].append(response.chat_message.content)

        if isinstance(response.chat_message, TextMessage):
            if response.chat_message.source == "LoopedAssistant":
                logger.warning("Reached the end of the conversation.")
                break

        counter += 1
        if counter > 8:
            break

    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
