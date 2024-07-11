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
        goal=f'Research the highest quality information related to: {query}, only focusing on techniques, tactics, and procedures that are good candidates for detections. Ensure the intel contains log source evidence information.',
        backstory="As a seasoned cyber threat researcher, you're at the forefront of identifying and analyzing emerging threats. Your expertise helps security teams write the best detection logic to catch threats. You focus on gathering actionable threat intel that includes clear log evidence for detection.",
        verbose=True,
        allow_delegation=False,
        llm=ChatOpenAI(model_name=openai_model),
        max_iter=5,
        tools=[exa_search_tool, scrape_website_tool]
    )

    analyst = Agent(
        role='Detection Engineer',
        goal='Analyze the information from the Cyber Threat Intelligence Researcher and select the highest quality candidates for detections. Ensure the information is sufficient to convert into detection logic, focusing on log source evidence.',
        backstory="With a keen eye for detail and a deep understanding of cyber threats, you excel at interpreting raw data and translating it into actionable detections for security operations teams. You prioritize threat intel that includes detailed log source evidence, ensuring the detection logic is robust and effective.",
        verbose=True,
        allow_delegation=True,
        llm=ChatOpenAI(model_name=openai_model),
        max_iter=5,
        tools=[exa_search_tool, scrape_website_tool]
    )

    # Define tasks
    research_task = Task(
        description=f"""Research and select the top 10 pieces of information related to: {query}. Follow these steps:
        1. Search for and gather detailed information from threat intelligence reports, cybersecurity blogs, and any relevant online sources describing real-world cyber incidents.
        2. Focus on identifying techniques, tactics, and procedures (TTPs) that are suitable candidates for detection.
        3. Ensure that each TTP includes clear log source evidence that can be used to write detection logic. Avoid atomic indicators of compromise.
        4. Some good examples are: threat hunting in Okta logs, TTPs used in AWS attacks, detection engineering in CloudTrail logs, hunting in SaaS logs, writing detections in Kubernetes audit logs, and detection engineering in EKS logs.
        5. Document each TTP with detailed descriptions, including the context of its use, how it manifests in logs, and why it is a good candidate for detection.

        The expected output is a comprehensive report detailing the top 10 threat intelligence findings, including:
        - Threat names and descriptions
        - Techniques, tactics, and procedures with log source evidence
        - Detailed context and usage information
        - Reasons why each TTP is a good candidate for detection.""",
        agent=researcher,
        expected_output="A comprehensive report detailing the top 10 threat intelligence findings, including threat names, descriptions, and log source evidence information.",
        tools=[exa_search_tool]
    )

    analysis_task = Task(
        description="""Analyze the research findings provided by the Cyber Threat Intelligence Researcher. Follow these steps:
        1. Carefully review the comprehensive report containing TTPs and behaviors.
        2. Identify and select the highest quality TTPs that would make great candidates for detection.
        3. Ensure each selected TTP includes sufficient log source information to be converted into detection logic.
        4. Prioritize TTPs that have clear and actionable log evidence, making them ideal for creating robust detection rules.
        5. Provide examples of good detection logic sources, such as sigma rules, Datadog OOTB rules, Panther Security content rules, Splunk security content, Elastic security content rules, and other open-source detection content.

        The expected output is a detailed analysis summarizing the threat intelligence, highlighting the best candidates for detection, and providing:
        - A summary of the selected TTPs
        - Detailed log source evidence for each TTP
        - Actionable insights and strategies for detection and mitigation""",
        agent=analyst,
        expected_output="A detailed analysis summarizing the threat intelligence, highlighting the best candidates for detection, with emphasis on actionable insights and log source evidence for detection and mitigation strategies."
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