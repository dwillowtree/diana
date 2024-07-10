import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from threat_research import perform_threat_research
import subprocess
import sys

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
[Numbered list of investigation steps from {previous_investigation_steps}]

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

# Custom CSS and JavaScript for improved styling and resizable sidebar
st.markdown("""
<style>
    .stApp {
        max-width: none;
        padding: 1rem;
    }
    .main .block-container {
        max-width: none;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .main-content {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
    }
    .sidebar .stButton>button {
        width: 100%;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    [data-testid="stSidebar"] {
        min-width: 300px;
        max-width: 800px;
        width: 300px;
        resize: horizontal;
        overflow: auto;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 100%;
        height: 100%;
    }
    .stApp > header {
        background-color: transparent;
    }
    .stApp {
        margin: 0;
    }
    .resize-handle {
        position: absolute;
        right: -5px;
        top: 0;
        bottom: 0;
        width: 10px;
        cursor: col-resize;
        z-index: 1000;
    }
</style>

<script>
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    sidebar.appendChild(resizeHandle);

    let isResizing = false;
    let lastDownX = 0;

    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        lastDownX = e.clientX;
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const offsetRight = document.body.offsetWidth - (e.clientX - document.body.offsetLeft);
        const minWidth = 300;
        const maxWidth = 800;
        const newWidth = Math.min(Math.max(minWidth, document.body.offsetWidth - offsetRight), maxWidth);
        sidebar.style.width = newWidth + 'px';
    });

    document.addEventListener('mouseup', (e) => {
        isResizing = false;
    });
</script>
""", unsafe_allow_html=True)

# Add a sidebar
sidebar = st.sidebar

with sidebar:
    st.image("https://i.imgur.com/wEHCCaj.png", width=300)
    st.markdown(
        """
        <div style="text-align: center;">
            Developed by Dylan Williams <a href="https://www.linkedin.com/in/dylan-williams-a2927599/" target="_blank">LinkedIn</a> | 
            <a href="https://github.com/dwillowtree/diana" target="_blank">GitHub Repository</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Quick Start Guide section (collapsed by default)
    with st.expander("Quick Start Guide", expanded=False):
        st.markdown("""
        DIANA (Detection and Intelligence Analysis for New Alerts) automates detection creation from threat intelligence.

        **Note: Providing high-quality example detections, logs, and your detection writing process is critical for optimal results.**

        ### Steps:
        1. Select LLM provider and model
        2. Choose security data/log type(s) for detection
        3. Select detection language
        4. Input threat TTPs description or upload report/blog post
        5. **Important:** Provide 3-7 diverse, high-quality example detections for the chosen log source
        6. **Important:** Provide 3-7 example log sources
        7. **Recommended:** Outline your typical detection writing steps (this helps DIANA follow your workflow)
        8. Describe alert triage/investigation steps
        9. Click 'Process Threat Intel'

        Remember: The quality and diversity of your inputs directly impact DIANA's output. Take time to provide comprehensive examples and follow your standard workflow for best results.
        """)
    # About DIANA section (collapsed by default)
    with st.expander("About DIANA", expanded=False):
        st.markdown("""
        DIANA (Detection and Intelligence Analysis for New Alerts) is an AI-powered tool designed to streamline the detection writing process in cybersecurity operations.

        ### Purpose:
        - Automate the creation of detections from threat intelligence
        - Reduce manual effort in researching log sources and writing queries
        - Generate investigation steps and quality assurance checks

        DIANA leverages advanced AI capabilities to enhance efficiency and accuracy in cybersecurity threat detection, allowing security teams to respond more quickly and effectively to emerging threats.
        """)
    st.subheader("Configuration")
    
    # LLM Provider selection with tooltip
    llm_provider = st.selectbox(
        "LLM Provider",
        ["OpenAI", "Anthropic"],
        key="llm_provider",
        help="Choose the AI model provider for processing."
    )
    
    # Model selection based on provider
    if llm_provider == "OpenAI":
        model = st.selectbox(
            "Model Type",
            ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            key="openai_model",
            help="Select the OpenAI model to use for processing."
        )
    else:
        model = st.selectbox(
            "Model Type",
            ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            key="anthropic_model",
            help="Select the Anthropic model to use for processing."
        )
    
    # Data types multiselect with search functionality
    data_types = st.multiselect(
        "Security Data/Log Type(s)",
        [
            "Okta Logs", "AWS CloudTrail Logs", "Kubernetes Audit Logs", "GitLab Audit Logs"
        ],
        default=["AWS CloudTrail Logs"],
        key="security_data_type",
        help="Select the relevant log types for your detection."
    )

    # Detection language selection with tooltip
    detection_language = st.selectbox(
        "Detection Language",
        [
            "AWS Athena", "StreamAlert", "Splunk SPL", "Elastic Query DSL",
            "Kusto Query Language (KQL)",
            "Sigma Rules","Panther Detection-as-Code (Python)"
        ],
        key="detection_language_select",
        help="Choose the query language for your detection rules."
    )

    # Model parameters with explanations
    st.subheader("Model Parameters")
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        key="temperature_slider",
        help="Controls output randomness. Lower values (e.g., 0.2) for more deterministic results, higher values (e.g., 0.8) for more creative outputs."
    )
    
    max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=4000,
        value=1000,
        step=100,
        key="max_tokens_slider",
        help="Maximum number of tokens in the generated response. Higher values allow for longer outputs but may increase processing time."
    )

    # Open Source Detection Content (collapsed by default)
    with st.expander("Open Source Detection Content", expanded=False):
        st.markdown("[![Elastic](https://img.shields.io/badge/Elastic-005571?style=for-the-badge&logo=elastic&logoColor=white)](https://github.com/elastic/detection-rules)")
        st.markdown("[![Chronicle](https://img.shields.io/badge/Chronicle-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://github.com/chronicle/detection-rules)")
        st.markdown("[![Sigma](https://img.shields.io/badge/Sigma-008080?style=for-the-badge&logo=sigma&logoColor=white)](https://github.com/SigmaHQ/sigma)")
        st.markdown("[![Hacking the Cloud](https://img.shields.io/badge/Hacking_the_Cloud-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://hackingthe.cloud/)")
        st.markdown("[![Wiz Threats](https://img.shields.io/badge/Wiz_Threats-00ADEF?style=for-the-badge&logo=wiz&logoColor=white)](https://threats.wiz.io/)")
        st.markdown("[![Anvilogic Armory](https://img.shields.io/badge/Anvilogic_Armory-6F2DA8?style=for-the-badge&logo=github&logoColor=white)](https://github.com/anvilogic-forge/armory)")

# Main content area
st.title("🛡️ D.I.A.N.A.")
st.subheader("Detection and Intelligence Analysis for New Alerts")

# Create tabs for main workflow and threat research
tab1, tab2 = st.tabs(["Detection Engineering", "Threat Research Crew"])

# Progress bar for multi-step process
if 'step' not in st.session_state:
    st.session_state.step = 0

# Function to update progress
def update_progress():
    # Cap the step at 5 for progress calculation
    capped_step = min(st.session_state.step, 5)
    progress_value = capped_step / 5
    progress_bar.progress(progress_value)
    
    # Display the actual step number, even if it's beyond 5
    step_counter.markdown(f"**Current Step: {st.session_state.step}/5**")
    
with tab1:
    # Create placeholders for the progress bar and step counter
    progress_bar = st.empty()
    step_counter = st.empty()

    # Update progress at the beginning
    update_progress()

# Main content layout
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Threat Intelligence Input")
        description = st.text_area(
            "Enter threat intelligence description:",
            height=200,
            value="Detect a user attempting to exfiltrate an Amazon EC2 AMI Snapshot. This rule lets you monitor the ModifyImageAttribute CloudTrail API calls to detect when an Amazon EC2 AMI snapshot is made public or shared with an AWS account. This rule also inspects: @requestParameters.launchPermission.add.items.group array to determine if the string all is contained. This is the indicator which means the RDS snapshot is made public. @requestParameters.launchPermission.add.items.userId array to determine if the string * is contained. This is the indicator which means the RDS snapshot was shared with a new or unknown AWS account.",
            help="Provide a detailed description of the threat intelligence you want to analyze."
        )
        uploaded_file = st.file_uploader(
            "Upload threat intel report or blog (optional)",
            type=["txt", "pdf"],
            help="You can optionally upload a threat intelligence report or blog post for analysis."
        )
        file_content = ""
        if uploaded_file is not None:
            file_content = uploaded_file.getvalue().decode("utf-8")

    with col2:
        st.subheader("Example Detections")
        num_detections = st.number_input("Number of example detections", min_value=1, value=3, step=1)
        current_detections = [
            st.text_area(
                f"Example detection {i+1}",
                height=100,
                value="SELECT sourceIPAddress, eventName, userAgent\nFROM cloudtrail_logs\nWHERE eventName = 'ConsoleLogin' AND errorMessage LIKE '%Failed authentication%'\nGROUP BY sourceIPAddress, eventName, userAgent\nHAVING COUNT(*) > 10",
                help="Provide an example of an existing detection query in your environment."
            ) for i in range(num_detections)
        ]
        
        st.subheader("Example Logs")
        num_logs = st.number_input("Number of example logs", min_value=1, value=3, step=1)
        example_logs = [
            st.text_area(
                f"Example log {i+1}",
                height=100,
                value="paste examples of your actual logs here, you may have different field names or logging structure",
                help="Provide examples of actual log entries from your environment."
            ) for i in range(num_logs)
        ]

    # Collapsible sections for additional inputs
    with st.expander("Detection Writing Steps", expanded=False):
        detection_steps = st.text_area(
            "Enter detection writing steps:",
            height=150,
            value="1. Identify the key indicators or behaviors from the threat intel\n2. Determine the relevant log sources and fields\n3. Write the query using the specified detection language\n4. Include appropriate filtering to reduce false positives\n5. Add comments to explain the logic of the detection",
            help="Outline the steps you typically follow when writing detection rules."
        )

    with st.expander("Alert Triage Steps", expanded=False):
        sop = st.text_area(
            "Enter standard operating procedures or investigation steps for your current detections and alerts:",
            height=150,
            value="1. Validate the alert by reviewing the raw log data\n2. Check for any related alerts or suspicious activities from the same source\n3. Investigate the affected systems and user accounts\n4. Determine the potential impact and scope of the incident\n5. Escalate to the incident response team if a true positive is confirmed",
            help="Describe your standard operating procedures for triaging and investigating alerts."
        )

    def run_threat_research(query):
        # Create a placeholder in the Streamlit UI
        output_placeholder = st.empty()

        # Run the threat_research.py script and capture its output
        process = subprocess.Popen(['python', 'threat_research.py', query], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)

        # Stream the output to the Streamlit UI
        full_output = ""
        for line in process.stdout:
            full_output += line
            output_placeholder.text_area("Research Progress:", full_output, height=400)

        # Return the final result
        return full_output

    if st.button("🚀 Process Threat Intel", type="primary") or st.session_state.step > 0:
        if not description and not uploaded_file and st.session_state.step == 0:
            st.error("Please provide either a threat intel description or upload a file.")
        else:
            if st.session_state.step == 0:
                # Step 1: Analyze Threat Intel
                st.subheader("Step 1: Analyze Threat Intel")
                details = st.expander("View Details", expanded=False)

                context = {
                    "description": description,
                    "file_content": file_content,
                    "data_types": ", ".join(data_types),
                }

                formatted_prompt = prompts[0].format(**context)

                with details:
                    st.text("Prompt:")
                    st.code(formatted_prompt, language="markdown")

                with st.spinner("Analyzing threat intelligence..."):
                    if llm_provider == "OpenAI":
                        result = process_with_openai(formatted_prompt, model, max_tokens, temperature)
                    else:
                        result = process_with_anthropic(formatted_prompt, model, max_tokens, temperature)

                if result is None:
                    st.error("An error occurred while analyzing the threat intelligence.")
                else:
                    # Store the result in session state
                    st.session_state.result = result

                    with details:
                        st.text("Result:")
                        st.code(st.session_state.result, language="markdown")

                    st.success("Analysis complete!")
                    st.session_state.step = 1
                    update_progress()

            if st.session_state.step >= 1:
                with st.spinner("Parsing detections..."):
                    # Parse the result to extract detections
                    detections = []
                    detection_names = []
                    threat_behaviors = []
                    current_detection = ""
                    current_threat_behavior = ""
                    capturing_threat_behavior = False

                    for line in st.session_state.result.split('\n'):
                        stripped_line = line.strip()
                        if stripped_line.startswith(("Detection Name:", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
                            if current_detection:
                                detections.append(current_detection.strip())
                                threat_behaviors.append(current_threat_behavior.strip())
                                current_detection = ""
                                current_threat_behavior = ""
                            name = stripped_line.split(":", 1)[-1].strip() if ":" in stripped_line else stripped_line.split(".", 1)[-1].strip()
                            name = name.lstrip("0123456789. ")
                            detection_names.append(name)
                        elif "Threat Behavior:" in stripped_line:
                            current_threat_behavior = stripped_line.split("Threat Behavior:", 1)[-1].strip()
                            capturing_threat_behavior = True
                        elif capturing_threat_behavior and any(stripped_line.startswith(x) for x in ["Log Evidence:", "Context:"]):
                            capturing_threat_behavior = False
                        elif capturing_threat_behavior:
                            current_threat_behavior += " " + stripped_line
                        current_detection += line + "\n"
                    
                    if current_detection:
                        detections.append(current_detection.strip())
                        threat_behaviors.append(current_threat_behavior.strip())

                    if not detection_names:
                        st.warning("No specific detections were identified. The entire analysis will be processed as a single detection.")
                        detection_names = ["Entire Analysis"]
                        detections = [st.session_state.result]
                        threat_behaviors = [""]

                    st.session_state.detections = detections
                    st.session_state.detection_names = detection_names
                    st.session_state.threat_behaviors = threat_behaviors

                # Display the number of detections found
                st.info(f"Number of detections found: {len(detection_names)}")

                # Display the names of the detections and their threat behaviors
                if len(detection_names) >= 1:
                    st.write("Detections found:")
                    for name, behavior in zip(detection_names, threat_behaviors):
                        st.markdown(f"**{name}**")
                        st.write(f"Threat Behavior: {behavior}")
                        st.write("---")

                # Allow user to select a detection
                st.session_state.selected_detection = st.selectbox("Select a detection to process:", st.session_state.detection_names)

                if st.button("Process Selected Detection"):
                    st.session_state.step = 2
                    update_progress()
            

            if st.session_state.step >= 2:
                # Process the remaining steps for the selected detection
                results = {}
                results[1] = st.session_state.result  # Store the first result

                for i in range(2, 6):
                    if st.session_state.step > i:
                        continue

                    step_name = ['Create Detection Rule', 'Develop Investigation Guide', 'Quality Assurance Review', 'Final Summary'][i-2]
                    
                    st.subheader(f"Step {i}: {step_name}")
                    details = st.expander("View Details", expanded=False)

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

                    with st.spinner(f"Processing {step_name}..."):
                        if llm_provider == "OpenAI":
                            result = process_with_openai(formatted_prompt, model, max_tokens, temperature)
                        else:
                            result = process_with_anthropic(formatted_prompt, model, max_tokens, temperature)

                    if result is None:
                        st.error(f"An error occurred while processing {step_name}.")
                        break

                    results[i] = result

                    with details:
                        st.text("Result:")
                        st.code(result, language="markdown")

                    st.success(f"{step_name} complete!")
                    st.session_state.step = i + 1
                    update_progress()

                if len(results) == 5:
                    st.session_state.step = 6  # Indicate completion
                    update_progress()
                    st.success("Processing complete!")
                    st.markdown(results[5])

                    # Add a button to restart the process
                    if st.button("Start Over"):
                        st.session_state.step = 0
                        update_progress()
                        st.experimental_rerun()
                else:
                    st.error("An error occurred while processing the threat intelligence.")

with tab2:
    # Threat Research section
    st.subheader("Threat Research Crew")
    
    st.markdown("""
    This feature spins up a crew of autonomous AI agents that perform threat detection research on your topic of choice. 
    
    These agents use Exa, which employs semantic search (embeddings) to search the web, providing more contextually relevant results than traditional keyword-based search engines like Google.
    
    **Examples of research topics:**
    - Threat hunting in Okta logs
    - Most common TTPs used by attackers in AWS
    - Latest detection strategies for ransomware in Windows environments
    """)

    research_query = st.text_input(
        "Enter your cybersecurity research topic:",
        placeholder="E.g., 'Threat hunting in Okta logs' or 'TTPs from CloudTrail logs used in AWS attacks'",
        help="Specify a topic for in-depth threat research to supplement your analysis."
    )

    if st.button("🔍 Perform Threat Research", key="research_button"):
        if research_query:
            with st.spinner("Performing threat research... This may take a few minutes."):
                research_result = run_threat_research(research_query)
            
            st.subheader("Threat Research Results")
            st.markdown(research_result)
            
            if st.button("Use Research in Analysis"):
                st.session_state.description = st.session_state.get('description', '') + f"\n\nAdditional Threat Research:\n{research_result}"
                st.success("Research results added to the analysis.")
        else:
            st.warning("Please enter a research topic before performing threat research.")

st.markdown("---")