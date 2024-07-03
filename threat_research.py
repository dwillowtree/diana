import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, EXASearchTool

# Load environment variables
load_dotenv()

def perform_threat_research(query):
    # Initialize tools
    search_tool = SerperDevTool()
    exa_search_tool = EXASearchTool()

    # Define agents
    researcher = Agent(
        role='Cyber Threat Researcher',
        goal=f'Uncover the latest threat intelligence related to: {query}',
        backstory="As a seasoned cyber threat researcher, you're at the forefront of identifying and analyzing emerging threats. Your expertise helps organizations stay ahead of potential security risks.",
        verbose=True,
        allow_delegation=True,
        tools=[exa_search_tool]
    )

    analyst = Agent(
        role='Threat Intelligence Analyst',
        goal=f'Analyze and summarize threat findings related to: {query}',
        backstory="With a keen eye for detail and a deep understanding of cyber threats, you excel at interpreting raw data and translating it into actionable intelligence for security teams.",
        verbose=True,
        allow_delegation=False,
        tools=[exa_search_tool]
    )

    # Define tasks
    research_task = Task(
        description=f"Research the latest threat intelligence related to: {query}. Focus on identifying TTPs, potential indicators of compromise, and overall threat landscape.",
        agent=researcher,
        expected_output="A comprehensive report detailing the latest threat intelligence findings, including TTPs and potential IoCs.",
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

# Example usage
if __name__ == "__main__":
    query = "threat hunting in Okta logs"
    result = perform_threat_research(query)
    print(result)