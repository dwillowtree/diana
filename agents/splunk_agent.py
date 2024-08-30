import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from agents.tools.splunk_search_tool import SplunkSearchTool 

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def perform_splunk_query_tuning(query, splunk_query):
    openai_model = os.getenv("OPENAI_MODEL_NAME", "gpt-4")

    # Initialize the Splunk query tool
    splunk_tool = SplunkSearchTool(splunk_base_url=os.getenv("SPLUNK_BASE_URL"), auth_token=os.getenv("SPLUNK_AUTH_TOKEN"))
    
    # Define agents
    query_tuner = Agent(
        role='Splunk Detection Optimization Specialist',
        goal=f'Enhance the Splunk detection query "{splunk_query}" by minimizing false positives and optimizing detection criteria tailored to the environment’s specific behaviors.',
        backstory=(
            "You are a seasoned Splunk detection engineer with expertise in cybersecurity, specializing in refining and tuning detection queries. "
            "Your primary objective is to optimize detection accuracy by carefully analyzing log data and adjusting queries to exclude benign activities "
            "or frequent noise that does not signify real threats. Your role involves applying advanced Splunk query techniques to balance detection efficacy with accuracy."
        ),
        verbose=True,
        allow_delegation=False,
        llm=ChatOpenAI(model_name=openai_model),
        tools=[splunk_tool]
    )

    # Define tasks
    tuning_task = Task(
        description=(
            f"Refine the provided Splunk detection query: {splunk_query}. The objective is to tune the query by identifying and excluding benign behaviors that may cause false positives. Follow these steps:\n"
            "1. Execute the Splunk detection query to retrieve relevant log data.\n"
            "2. Thoroughly examine the query results to identify patterns and repetitive benign behaviors, such as routine actions by specific users or systems.\n"
            "3. Use findings from the log analysis to refine the query. For example, exclude specific AWS accounts (e.g., 'sandbox-dev', 'sandbox-dev2') that frequently perform non-malicious actions like disabling GuardDuty detectors.\n"
            "4. Apply advanced query tuning techniques, such as adjusting filters, refining time windows, and modifying event correlation rules to enhance detection accuracy.\n"
            "5. Validate the updated query to ensure it effectively identifies real threats while excluding identified benign behaviors.\n"
            "6. Document all changes made to the query, including the rationale for each modification, any assumptions about benign patterns, and potential impacts on detection coverage."
        ),
        agent=query_tuner,
        expected_output=(
            "A refined Splunk detection query that minimizes false positives, along with comprehensive documentation detailing the changes made, identified benign behaviors excluded, and any trade-offs in detection efficacy."
        ),
    )

    # Create the crew
    crew = Crew(
        agents=[query_tuner],
        tasks=[tuning_task],
        process=Process.sequential,
        verbose=2  # Increased verbosity for more detailed output
    )

    # Kick off the tuning process
    result = crew.kickoff(inputs={'query': splunk_query})
    return result

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
