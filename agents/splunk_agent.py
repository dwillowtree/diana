import os
import logging
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from agents.tools.splunk_search_tool import SplunkSearchTool 

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def perform_splunk_query_tuning(task: str, splunk_query: str, max_iterations: int = 3):
    splunk_base_url = os.getenv("SPLUNK_BASE_URL")
    auth_token = os.getenv("SPLUNK_AUTH_TOKEN")

    if not splunk_base_url or not auth_token:
        raise ValueError("SPLUNK_BASE_URL and SPLUNK_AUTH_TOKEN must be set in the environment variables")

    splunk_tool = SplunkSearchTool(splunk_base_url=splunk_base_url, auth_token=auth_token)
    
    # Define agent
    query_tuner = Agent(
        role='Splunk Detection Optimization Specialist',
        goal=f'Enhance the Splunk detection query "{splunk_query}" by minimizing false positives and optimizing detection criteria.',
        backstory="You are a seasoned Splunk detection engineer specializing in refining and tuning detection queries.",
        verbose=True,
        allow_delegation=False,
        llm=ChatOpenAI(model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4")),
        tools=[splunk_tool]
    )

    # Define task
    tuning_task = Task(
        description=(
            f"Refine the Splunk detection query: {splunk_query}. Follow these steps:\n"
            "1. Validate and execute the initial query.\n"
            "2. Analyze results to identify benign behavior and false positives.\n"
            "3. Modify the query to exclude identified benign behaviors.\n"
            "4. Re-run and validate the modified query.\n"
            "5. Repeat steps 2-4 until optimized or max iterations reached.\n"
            "6. Document all changes, rationale, and potential impacts."
        ),
        agent=query_tuner,
        expected_output="A refined Splunk query with documentation of changes and their rationale."
    )

    # Create crew
    crew = Crew(
        agents=[query_tuner],
        tasks=[tuning_task],
        process=Process.sequential,
        verbose=2
    )

    # Iterative refinement process
    current_query = splunk_query
    for iteration in range(max_iterations):
        logging.info(f"Starting iteration {iteration + 1} of query tuning")
        result = crew.kickoff(inputs={'query': current_query})
        
        # Extract the refined query from the result
        refined_query = extract_refined_query(result)
        
        if not refined_query or refined_query == current_query:
            logging.info("No further refinements made. Tuning complete.")
            break
        
        current_query = refined_query
        logging.info(f"Refined query: {current_query}")

    return {"final_query": current_query, "tuning_process": result}

def extract_refined_query(result):
    if isinstance(result, dict):
        return result.get('refined_query', '')
    elif isinstance(result, str):
        # Attempt to find a refined query in the string
        # This is a simple example; you might need to adjust based on the actual output format
        if "refined query:" in result.lower():
            return result.split("refined query:", 1)[1].strip()
    return ''

# Modified main block for subprocess compatibility
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        query = sys.argv[1]
        splunk_query = sys.argv[2]
        print(f"Starting Splunk query tuning for query: {query} and Splunk query: {splunk_query}")
        result = perform_splunk_query_tuning(query, splunk_query)
        print("Tuning completed. Final result:")
        print(result)
    else:
        print("Please provide both a general query and a Splunk detection query as command-line arguments.")
