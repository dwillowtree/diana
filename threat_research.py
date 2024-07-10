import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, EXASearchTool, ScrapeWebsiteTool

# Load environment variables
load_dotenv()

def perform_threat_research(query):

    openai_model = os.getenv("OPENAI_MODEL_NAME", "gpt-4")
    # Initialize tools
    exa_search_tool = EXASearchTool()
    scrape_website_tool = ScrapeWebsiteTool()

    # Define agents
    researcher = Agent(
        role='Cyber Threat Intelligence Researcher',
        goal=f'Research the highest quality threat intelligence related to: {query}, only focusing on techniques, tactics, and procedures.',
        backstory="As a seasoned cyber threat researcher, you're at the forefront of identifying and analyzing emerging threats. Your expertise helps security teams write the best detection logic to catch threats.",
        verbose=True,
        allow_delegation=True,
        llm=ChatOpenAI(model_name=openai_model),
        max_iter=5,
        tools=[exa_search_tool, scrape_website_tool]
    )

    analyst = Agent(
        role='Threat Intelligence Analyst',
        goal=f'Analyze and summarize threat findings related to: {query}',
        backstory="With a keen eye for detail and a deep understanding of cyber threats, you excel at interpreting raw data and translating it into actionable intelligence for security teams.",
        verbose=True,
        allow_delegation=False,
        llm=ChatOpenAI(model_name=openai_model),
        max_iter=5,
        tools=[exa_search_tool, scrape_website_tool]
    )

    # Define tasks
    research_task = Task(
        description=f"Research the latest threat intelligence related to: {query}. Only focus on identifying TTPs and behaviors that have clear log evidence so they can be used to write detections.",
        agent=researcher,
        expected_output="A comprehensive report detailing the latest threat intelligence findings, including threat names and descriptions.",
        tools=[exa_search_tool]
    )

    analysis_task = Task(
        description="Analyze the research findings and create a summarized report. Highlight key points relevant to detection creation and threat mitigation.",
        agent=analyst,
        expected_output="A detailed analysis summarizing the threat intelligence, with emphasis on actionable insights for detection and mitigation strategies."
        
    )

    # Create the crew
    crew = Crew(
        agents=[researcher, analyst],
        tasks=[research_task, analysis_task],
        process=Process.sequential,
        verbose=2  # Increased verbosity for more detailed output
    )

    # Kick off the research process
    result = crew.kickoff(inputs={'query': query})
    return result

# Modified main block for subprocess compatibility
if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"Starting threat research for query: {query}")
        result = perform_threat_research(query)
        print("Research completed. Final result:")
        print(result)
    else:
        print("Please provide a query as a command-line argument.")