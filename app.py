import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from threat_research import perform_threat_research

# Load environment variables
load_dotenv()

# Set up OpenAI and Anthropic clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

def process_with_openai(prompt, model, max_tokens, temperature):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error with OpenAI API: {str(e)}")
        return None

def process_with_anthropic(prompt, model, max_tokens, temperature):
    try:
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        st.error(f"Error with Anthropic API: {str(e)}")
        return None

# Prompts for each step of the process
prompts = [
    # Prompt 1: Analyze threat intelligence
    """You are an expert cyber security threat intelligence analyst. 
    The intel will be provided to you in the form of incident reports, threat intel reports, cyber security blogs, adverary emulation tools, existing detection content, or any description in natural language
    of techniques, tactics and procedures (TTPs) used by cyber security threat actors. Avoid using atomic indicators like IP addresses or domain names. Focus only on behaviors or techniques.
    Analyze the following threat intelligence:

Description: {description}
Blog/Report (if available): {file_content}

Focus only on threat intelligence that can be used to write detections for {data_types}. Extract potential detections that have clear log evidence in the provided intelligence.
For each potential detection:
1. Provide a concise name
2. Write a detailed description of the threat behavior
3. List the specific log data or events that would be used in the detection
4. Include any relevant context or prerequisites for the detection

Format your analysis as a numbered list:

1. Detection Name: [Concise name]
   Threat Behavior: [Detailed description]
   Log Evidence: [Specific log data or events]
   Context: [Any relevant prerequisites or environmental factors]

If no detections are found for the specified data sources, clearly state this.""",
    # Prompt 2: Create detection rule
    """As a detection engineer specializing in {detection_language}, create a robust detection rule based on the following analysis:
{previous_analysis}

Additional context:
- Example detections: {current_detections}
- Log examples: {example_logs}
- Detection steps (if any): {detection_steps}

Your task:
1. Write a detection rule in {detection_language} that accurately captures the threat behavior
2. Ensure the rule uses the specific log data identified in the analysis
3. Include comments explaining the logic and any assumptions made

If a complete detection cannot be written, explain why and specify any missing information.

Present the final detection rule in a code block, followed by:
- Explanation of the rule's logic
- Any limitations or edge cases
- Estimated false positive rate and rationale""",

    # Prompt 3: Develop investigation guide
    """As an experienced SOC analyst, create a detailed investigation guide for the following detection rule:

{previous_detection_rule}

Use Palantir's alert and detection strategy framework and incorporate elements from this standard operating procedure (if provided): {sop}

Your investigation guide should include:
1. Initial triage steps to quickly assess the alert's validity
2. Detailed investigation procedures, including specific queries or commands
3. Criteria for escalation or closure of the alert
4. Potential related TTPs or lateral movement to look for
5. Recommended containment or mitigation actions

Format the guide as a numbered list with clear, concise, and actionable steps. Include any caveats, limitations, or decision points an analyst might encounter.""",

    # Prompt 4: Quality assurance review
    """As a QA specialist in cyber threat detection, conduct a comprehensive review of the following detection rule and investigation steps:

Detection Rule:
{previous_detection_rule}

Investigation Steps:
{previous_investigation_steps}

Assess the following aspects:
1. Accuracy: Does the rule correctly interpret the threat intelligence?
2. Completeness: Does the detection logic cover all aspects of the threat behavior?
3. Efficiency: Is the detection optimized for performance in the target environment?
4. False Positive Rate: Provide a realistic estimate and justification
5. Clarity: Are the investigation steps clear, comprehensive, and actionable?
6. Coverage: Do the steps adequately cover validation, investigation, and response?

For each aspect, provide:
- A rating (Excellent, Good, Needs Improvement, or Poor)
- Specific recommendations for improvement
- If no changes are needed, a brief justification for why the current version is optimal

Present your QA findings as a structured report with clear recommendations for each aspect.""",

    # Prompt 5: Final summary
    """As a senior threat analyst, compile a comprehensive detection package using the following components:

Detection Rule:
{previous_detection_rule}

Investigation Steps:
{previous_investigation_steps}

QA Findings:
{previous_qa_findings}

Create a markdown-formatted output with the following structure:

# [Threat TTP Name]: [Detection Rule Name]

## Threat Description
[Concise description of the threat behavior this detection aims to identify]

## Detection Rule
{detection_language}
{previous_detection_rule}

Log Sources
[List of specific log sources or data types required for this detection]

Investigation Steps
[Numbered list of investigation steps from Prompt 3]

Performance Considerations
[Brief notes on expected performance, including estimated false positive rate]

QA Notes
[Summary of key QA findings and any outstanding items to address]

Ensure the final output is well-structured, comprehensive, and ready for review and implementation by the security operations team."""

]

def process_threat_intel(description, file_content, llm_provider, model, data_types, detection_language, current_detections, example_logs, detection_steps, sop, max_tokens, temperature):
    results = {}
    for i, prompt in enumerate(prompts, 1):
        context = {
            "description": description,
            "file_content": file_content,
            "data_types": ", ".join(data_types),
            "detection_language": detection_language,
            "current_detections": "\n".join(current_detections),
            "example_logs": "\n".join(example_logs),
            "detection_steps": detection_steps,
            "sop": sop,
            "previous_analysis": result if selected_detection == "Entire Analysis" else next((d for d in detections if selected_detection in d), st.session_state.result),
            "previous_detection_rule": results.get(2, ""),
            "previous_investigation_steps": results.get(3, ""),
            "previous_qa_findings": results.get(4, "")
        }
        
        formatted_prompt = prompt.format(**context)
        
        if llm_provider == "OpenAI":
            result = process_with_openai(formatted_prompt, model, max_tokens, temperature)
        else:
            result = process_with_anthropic(formatted_prompt, model, max_tokens, temperature)
        
        if result is None:
            return None

        results[i] = result
    
    return results

# Streamlit UI
st.set_page_config(page_title="D.I.A.N.A.", page_icon="🛡️", layout="wide")

# Add a sidebar
sidebar = st.sidebar

with sidebar:
    st.image("https://i.imgur.com/wEHCCaj.png", width=300)  # Add your logo

    # Add the About DIANA section
    st.markdown("""
    ## About DIANA

    DIANA (Detection and Intelligence Analysis for New Alerts) is an AI-powered tool designed to streamline the detection writing process in cybersecurity operations.

    ### Purpose:
    - Automate the creation of detections from threat intelligence
    - Reduce manual effort in researching log sources and writing queries
    - Generate investigation steps and quality assurance checks

    ### How to Use:
    1. Select your LLM provider and model
    2. Choose relevant security data/log types
    3. Enter threat intelligence description or upload a report
    4. Provide example detections and writing steps
    5. Add standard operating procedures
    6. Adjust model parameters if needed
    7. Click 'Process Threat Intel' to generate results

    DIANA will guide you through the entire process, from threat analysis to final detection creation, saving time and improving efficiency in your security operations.
    """)

    st.subheader("Configuration")
    llm_provider = st.selectbox("LLM Provider", ["OpenAI", "Anthropic"], key="llm_provider")
    
    if llm_provider == "OpenAI":
        model = st.selectbox("Model Type", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"], key="openai_model")
    else:
        model = st.selectbox("Model Type", ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"], key="anthropic_model")
    
    data_types = st.multiselect("Security Data/Log Type(s)", [
        "Okta Logs", 
        "AWS CloudTrail Logs", 
        "Kubernetes Audit Logs", 
        "GitLab Audit Logs",
        "Azure Activity Logs",
        "Google Cloud Audit Logs",
        "Microsoft 365 Audit Logs",
        "Cloudflare Logs",
        "Docker Container Logs",
        "AWS GuardDty Findings",
        "AWS VPC Flow Logs",
        "Azure Sentinel Logs",
        "Google Cloud Security Command Center Logs",
        "GitHub Audit Logs",
        "Salesforce Event Monitoring Logs"
    ], default=["AWS CloudTrail Logs"], key="security_data_type")

    detection_language = st.selectbox("Detection Language", [
        "AWS Athena", 
        "StreamAlert", 
        "Splunk SPL", 
        "Elastic Query DSL",
        "Kusto Query Language (KQL)",
        "Google Cloud Logging Query Language",
        "Sigma Rules",
        "YARA Rules",
        "Open Policy Agent (OPA) Rego",
        "AWS Security Hub Custom Insights",
        "Falco Rules",
        "Panther Detection-as-Code (Python)",
        "Sumo Logic Search Query Language",
        "Datadog Security Rules"
    ], key="detection_language_select")

    st.subheader("Model Parameters")
    st.write("Temperature: Controls the randomness of the output. Higher values (e.g., 0.8) make the output more random, while lower values (e.g., 0.2) make it more deterministic.")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1, key="temperature_slider")
    
    st.write("Max Tokens: The maximum number of tokens (words or word pieces) in the generated response. Higher values allow for longer outputs but may increase processing time.")
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=4000, value=1000, step=100, key="max_tokens_slider")

    st.subheader("Open Source Detection Content")
    st.markdown("[![Elastic](https://img.shields.io/badge/Elastic-005571?style=for-the-badge&logo=elastic&logoColor=white)](https://github.com/elastic/detection-rules)")
    st.markdown("[![Chronicle](https://img.shields.io/badge/Chronicle-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://github.com/chronicle/detection-rules)")
    st.markdown("[![Sigma](https://img.shields.io/badge/Sigma-008080?style=for-the-badge&logo=sigma&logoColor=white)](https://github.com/SigmaHQ/sigma)")
    st.markdown("[![Hacking the Cloud](https://img.shields.io/badge/Hacking_the_Cloud-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://hackingthe.cloud/)")
    st.markdown("[![Wiz Threats](https://img.shields.io/badge/Wiz_Threats-00ADEF?style=for-the-badge&logo=wiz&logoColor=white)](https://threats.wiz.io/)")
    st.markdown("[![Anvilogic Armory](https://img.shields.io/badge/Anvilogic_Armory-6F2DA8?style=for-the-badge&logo=github&logoColor=white)](https://github.com/anvilogic-forge/armory)")

st.title("🛡️ D.I.A.N.A.")
st.subheader("Detection and Intelligence Analysis for New Alerts")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Threat Intelligence Input")
    description = st.text_area("Enter threat intelligence description:", 
                               height=200, 
                               value="Detect a user attempting to exfiltrate an Amazon EC2 AMI Snapshot.This rule lets you monitor the ModifyImageAttribute CloudTrail API calls to detect when an Amazon EC2 AMI snapshot is made public or shared with an AWS account.This rule also inspects: @requestParameters.launchPermission.add.items.group array to determine if the string all is contained. This is the indicator which means the RDS snapshot is made public.@requestParameters.launchPermission.add.items.userId array to determine if the string * is contained. This is the indicator which means the RDS snapshot was shared with a new or unknown AWS account.")
    uploaded_file = st.file_uploader("Upload threat intel report or blog (optional)", type=["txt", "pdf"])
    file_content = ""
    if uploaded_file is not None:
        file_content = uploaded_file.getvalue().decode("utf-8")

with col2:
    st.subheader("Example Detections")
    num_detections = st.number_input("Number of example detections", min_value=1, value=3, step=1)
    current_detections = [st.text_area(f"Example detection {i+1}", 
                                       height=100, 
                                       value="SELECT sourceIPAddress, eventName, userAgent\nFROM cloudtrail_logs\nWHERE eventName = 'ConsoleLogin' AND errorMessage LIKE '%Failed authentication%'\nGROUP BY sourceIPAddress, eventName, userAgent\nHAVING COUNT(*) > 10") for i in range(num_detections)]
    st.subheader("Example Logs")
    num_logs = st.number_input("Number of example logs", min_value=1, value=3, step=1)
    example_logs = [st.text_area(f"Example log {i+1}", 
                                 height=100, 
                                 value="paste examples of your actual logs here, you may have different field names or logging structure") for i in range(num_logs)]

st.subheader("Detection Writing Steps")
detection_steps = st.text_area("Enter detection writing steps:", 
                               height=150, 
                               value="1. Identify the key indicators or behaviors from the threat intel\n2. Determine the relevant log sources and fields\n3. Write the query using the specified detection language\n4. Include appropriate filtering to reduce false positives\n5. Add comments to explain the logic of the detection")

st.subheader("Alert Triage Steps")
sop = st.text_area("Enter standard operating procedures or investigation steps for your current detections and alerts:", 
                   height=150, 
                   value="1. Validate the alert by reviewing the raw log data\n2. Check for any related alerts or suspicious activities from the same source\n3. Investigate the affected systems and user accounts\n4. Determine the potential impact and scope of the incident\n5. Escalate to the incident response team if a true positive is confirmed")



# Your existing imports and function definitions go here

# Initialize session state variables
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'result' not in st.session_state:
    st.session_state.result = None
if 'detections' not in st.session_state:
    st.session_state.detections = []
if 'detection_names' not in st.session_state:
    st.session_state.detection_names = []
if 'selected_detection' not in st.session_state:
    st.session_state.selected_detection = None

# Your existing code for sidebar and input fields goes here

# Add a text input for the research query
research_query = st.text_input("Enter your cybersecurity research topic:", 
                               placeholder="E.g., 'threat hunting in Okta logs' or 'TTPs from CloudTrail logs used in AWS attacks'")

# Add new button for CrewAI threat research
if st.button("🔍 Perform Threat Research"):
    if research_query:
        with st.spinner("Performing threat research... This may take a few minutes."):
            research_result = perform_threat_research(research_query)
        
        st.subheader("Threat Research Results")
        st.markdown(research_result)  # Using markdown for better formatting
        
        # Option to use research results in analysis
        if st.button("Use Research in Analysis"):
            # Append research results to the description or file_content
            st.session_state.description = st.session_state.get('description', '') + f"\n\nAdditional Threat Research:\n{research_result}"
            st.success("Research results added to the analysis.")
    else:
        st.warning("Please enter a research topic before performing threat research.")

if st.button("🚀 Process Threat Intel", type="primary") or st.session_state.step > 0:
    if not description and not uploaded_file and st.session_state.step == 0:
        st.error("Please provide either a threat intel description or upload a file.")
    else:
        if st.session_state.step == 0:
            # Step 1: Analyze Threat Intel
            st.subheader("Step 1: Analyze Threat Intel")
            status = st.empty()
            details = st.expander("View Details", expanded=False)

            status.text("⏳ Running...")

            context = {
                "description": description,
                "file_content": file_content,
                "data_types": ", ".join(data_types),
            }

            formatted_prompt = prompts[0].format(**context)

            with details:
                st.text("Prompt:")
                st.code(formatted_prompt, language="markdown")

            if llm_provider == "OpenAI":
                result = process_with_openai(formatted_prompt, model, max_tokens, temperature)
            else:
                result = process_with_anthropic(formatted_prompt, model, max_tokens, temperature)

            if result is None:
                st.error("An error occurred while analyzing the threat intelligence.")
            else:
                # Store the result in session state
                st.session_state.result = result
                # Add debug output here
                st.subheader("Debug: Raw result from threat intelligence analysis")
                st.code(st.session_state.result, language="markdown")

                with details:
                    st.text("Result:")
                    st.code(st.session_state.result, language="markdown")

                status.text("✅ Done")
                st.session_state.step = 1

        if st.session_state.step >= 1:
            # Parse the result to extract detections
            detections = []
            detection_names = []
            current_detection = ""
            for line in st.session_state.result.split('\n'):
                if line.strip().startswith(("Detection Name:", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
                    if current_detection:
                        detections.append(current_detection.strip())
                        current_detection = ""
                    name = line.split(":", 1)[-1].strip() if ":" in line else line.split(".", 1)[-1].strip()
                    name = name.lstrip("0123456789. ")
                    detection_names.append(name)
                current_detection += line + "\n"
            
            if current_detection:
                detections.append(current_detection.strip())

            if not detection_names:
                st.warning("No specific detections were identified. The entire analysis will be processed as a single detection.")
                detection_names = ["Entire Analysis"]
                detections = [st.session_state.result]

            st.session_state.detections = detections
            st.session_state.detection_names = detection_names

            # Display the number of detections found
            st.info(f"Number of detections found: {len(detection_names)}")

            # Optionally, display the names of the detections
            if len(detection_names) > 1:
                st.write("Detections found:")
                for name in detection_names:
                    st.write(f"- {name}")

            # Allow user to select a detection
            st.session_state.selected_detection = st.selectbox("Select a detection to process:", st.session_state.detection_names)

            if st.button("Process Selected Detection"):
                st.session_state.step = 2

        if st.session_state.step >= 2:
            # Process the remaining steps for the selected detection
            results = {}
            results[1] = st.session_state.result  # Store the first result

            for i in range(2, 6):
                if st.session_state.step > i:
                    continue

                step_name = ['Create Detection Rule', 'Develop Investigation Guide', 'Quality Assurance Review', 'Final Summary'][i-2]
                
                st.subheader(f"Step {i}: {step_name}")
                status = st.empty()
                details = st.expander("View Details", expanded=False)

                status.text("⏳ Running...")

                context = {
                    "detection_language": detection_language,
                    "current_detections": "\n".join(current_detections),
                    "example_logs": "\n".join(example_logs),
                    "detection_steps": detection_steps,
                    "sop": sop,
                    "previous_analysis": next((d for d in st.session_state.detections if st.session_state.selected_detection in d), st.session_state.result),
                    "previous_detection_rule": results.get(2, ""),
                    "previous_investigation_steps": results.get(3, ""),
                    "previous_qa_findings": results.get(4, "")
                }

                formatted_prompt = prompts[i-1].format(**context)

                with details:
                    st.text("Prompt:")
                    st.code(formatted_prompt, language="markdown")

                if llm_provider == "OpenAI":
                    result = process_with_openai(formatted_prompt, model, max_tokens, temperature)
                else:
                    result = process_with_anthropic(formatted_prompt, model, max_tokens, temperature)

                if result is None:
                    status.error(f"An error occurred at step {i}.")
                    st.error(f"An error occurred while processing step {i}.")
                    break

                results[i] = result

                with details:
                    st.text("Result:")
                    st.code(result, language="markdown")

                status.text("✅ Done")
                st.session_state.step = i + 1

            if len(results) == 5:
                st.success("Processing complete!")
                st.markdown(results[5])
            else:
                st.error("An error occurred while processing the threat intelligence.")

# Your existing footer code goes here

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        Developed by Dylan Williams <a href="https://www.linkedin.com/in/dylan-williams-a2927599/" target="_blank">LinkedIn</a> | 
        <a href="https://github.com/dwillowtree/diana" target="_blank">GitHub Repository</a>
    </div>
    """,
    unsafe_allow_html=True
)