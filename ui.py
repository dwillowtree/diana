import subprocess
import sys
import streamlit as st
from dotenv import load_dotenv
import os
import fitz
from threat_research import perform_threat_research
from firecrawl_integration import scrape_url

# Load environment variables
load_dotenv()

def render_ui(prompts, process_with_llm):
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
            ["OpenAI", "Anthropic", "Amazon Bedrock", "Groq"],
            index=1,
            key="llm_provider",
            help="Choose the AI model provider for processing."
        )

        # Add Pro Tip before the model type selection
        st.sidebar.markdown("**PRO TIP:** Use Claude 3 Haiku (it's smart, fast, and cheap)")

        # Model selection based on provider
        if llm_provider == "OpenAI":
            model = st.selectbox(
                "Model Type",
                ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                key="openai_model",
                help="Select the OpenAI model to use for processing."
            )
        elif llm_provider == "Anthropic":
            model = st.selectbox(
                "Model Type",
                ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                index=2, 
                key="anthropic_model",
                help="Select the Anthropic model to use for processing."
            )
        elif llm_provider == "Amazon Bedrock":
            model = st.selectbox(
                "Model Type",
                [
                    "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
                    "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
                    "bedrock/meta.llama3-8b-instruct-v1:0",
                    "bedrock/meta.llama3-70b-instruct-v1:0"
                ],
                key="bedrock_model",
                help="Select the Amazon Bedrock model to use for processing."
            )
        elif llm_provider == "Groq":
            model = st.selectbox(
                "Model Type",
        [
            "groq/llama-3.1-70b-versatile",
            "groq/llama-3.1-8b-instant",
            "groq/llama3-8b-8192",
        ],
        key="groq_model",
        help="Select the Groq model to use for processing."
    )
        
        # Data types multiselect with search functionality
        data_types = st.multiselect(
            "Security Data/Log Type(s)",
            [
                "Okta Logs", "AWS CloudTrail Logs", "Kubernetes Audit Logs", "GitLab Audit Logs", "AWS EKS Plane logs", "Cisco Duo Logs"
            ],
            default=["AWS CloudTrail Logs"],
            key="security_data_type",
            help="Select the relevant log types for your detection."
        )

        # Detection language selection with tooltip
        detection_language = st.selectbox(
            "Detection Language",
            [
                "AWS Athena", "StreamAlert", "Splunk SPL", "Falcon LogScale", "Elastic Query DSL",
                "Kusto Query Language (KQL)",
                "Sigma Rules","Panther (Python)", "Hunters (Snowflake SQL)"
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
            value=0.1,
            step=0.1,
            key="temperature_slider",
            help="Controls output randomness. Lower values (e.g., 0.2) for more deterministic results, higher values (e.g., 0.8) for more creative outputs."
        )
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=4000,
            step=100,
            key="max_tokens_slider",
            help="Maximum number of tokens in the generated response. Higher values allow for longer outputs but may increase processing time."
        )
    
    st.title("🛡️ D.I.A.N.A.")
    st.subheader("Detection and Intelligence Analysis for New Alerts")


    # Create tabs for main workflow and threat research
    tab1, tab2, tab3 = st.tabs(["Detection Engineering", "Threat Research Crew", "Bulk Detection Processing [Coming Soon]"])

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
            url = st.text_input("Enter URL:")
            
            # Initialize session state for scraped content if it doesn't exist
            if 'scraped_content' not in st.session_state:
                st.session_state.scraped_content = ""

            # Scrape URL button
            if st.button("🔍 Scrape URL", type="primary"):  
                if url:
                    try:
                        with st.spinner("Scraping URL..."):
                            st.session_state.scraped_content = scrape_url(url)
                        st.success("URL scraped successfully!")
                    except Exception as e:
                        st.error(f"Error scraping URL: {e}")
                        st.session_state.scraped_content = ""
                else:
                    st.warning("Please enter a URL to scrape.")

            # Display scraped content if available
            if st.session_state.scraped_content:
                with st.expander("View Scraped Content", expanded=False):
                    st.markdown(st.session_state.scraped_content)
            
            description = st.text_area(
                "Enter threat intelligence description:",
                height=100,
                placeholder="Detect a user attempting to exfiltrate an Amazon EC2 AMI Snapshot. This rule lets you monitor the ModifyImageAttribute CloudTrail API calls to detect when an Amazon EC2 AMI snapshot is made public or shared with an AWS account. This rule also inspects: @requestParameters.launchPermission.add.items.group array to determine if the string all is contained. This is the indicator which means the RDS snapshot is made public. @requestParameters.launchPermission.add.items.userId array to determine if the string * is contained. This is the indicator which means the RDS snapshot was shared with a new or unknown AWS account.",
                help="Provide a detailed description of the threat intelligence you want to analyze."
            )
            uploaded_file = st.file_uploader(
                "Upload threat intel report or blog (optional)",
                type=["txt", "pdf"],
                help="You can optionally upload a threat intelligence report or blog post for analysis."
            )

            file_content = ""

            if uploaded_file is not None:
                if uploaded_file.type == "application/pdf":
                    # Process PDF file
                    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    for page_num in range(pdf_document.page_count):
                        page = pdf_document.load_page(page_num)
                        file_content += page.get_text()
                else:
                    # Process other text files
                    file_content = uploaded_file.getvalue().decode("utf-8")

                    # Collapsible sections for additional inputs
            with st.expander("Detection Writing Steps", expanded=False):
                detection_steps = st.text_area(
                    "Enter detection writing steps:",
                    height=150,
                    placeholder="1. Identify the key indicators or behaviors from the threat intel\n2. Determine the relevant log sources and fields\n3. Write the query using the specified detection language\n4. Include appropriate filtering to reduce false positives\n5. Add comments to explain the logic of the detection",
                    help="Outline the steps you typically follow when writing detection rules."
                )

            with st.expander("Alert Triage Steps", expanded=False):
                sop = st.text_area(
                    "Enter standard operating procedures or investigation steps for your current detections and alerts:",
                    height=150,
                    placeholder="1. Validate the alert by reviewing the raw log data\n2. Check for any related alerts or suspicious activities from the same source\n3. Investigate the affected systems and user accounts\n4. Determine the potential impact and scope of the incident\n5. Escalate to the incident response team if a true positive is confirmed",
                    help="Describe your standard operating procedures for triaging and investigating alerts."
                )    

        with col2:
            st.subheader("Example Detections")
            num_detections = st.number_input("Number of example detections", min_value=1, value=2, step=1)
            current_detections = [
                st.text_area(
                    f"Example detection {i+1}",
                    height=100,
                    placeholder="SELECT sourceIPAddress, eventName, userAgent\nFROM cloudtrail_logs\nWHERE eventName = 'ConsoleLogin' AND errorMessage LIKE '%Failed authentication%'\nGROUP BY sourceIPAddress, eventName, userAgent\nHAVING COUNT(*) > 10",
                    help="Provide an example of an existing detection query in your environment."
                ) for i in range(num_detections)
            ]
            
            st.subheader("Example Logs")
            num_logs = st.number_input("Number of example logs", min_value=1, value=2, step=1)
            example_logs = [
                st.text_area(
                    f"Example log {i+1}",
                    height=100,
                    placeholder="paste examples of your actual logs here, you may have different field names or logging structure",
                    help="Provide examples of actual log entries from your environment."
                ) for i in range(num_logs)
            ]

        def run_threat_research(query, crewai_model):
            # Create a placeholder in the Streamlit UI
            output_placeholder = st.empty()

            # Prepare the environment variables
            env = os.environ.copy()
            env["OPENAI_MODEL_NAME"] = crewai_model

            # Run the threat_research.py script and capture its output
            process = subprocess.Popen(['python', 'threat_research.py', query], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True,
                                    env=env)

            # Stream the output to the Streamlit UI
            full_output = ""
            for line in process.stdout:
                full_output += line
                output_placeholder.text_area("Research Progress:", full_output, height=400)

            # Return the final result
            return full_output

        # Process Threat Intel button
        if st.button("🚀 Process Threat Intel", type="primary") or st.session_state.step > 0:
            if not description and not uploaded_file and not st.session_state.scraped_content and st.session_state.step == 0:
                st.error("Please provide either a threat intel description or upload a file.")
            else:
                if st.session_state.step == 0:
                    # Step 1: Analyze Threat Intel
                    st.subheader("Step 1: Analyze Threat Intel")
                    details = st.expander("View Details", expanded=False)

                    context = {
                        "description": description,
                        "file_content": file_content,
                        "scraped_content": st.session_state.scraped_content,
                        "data_types": ", ".join(data_types),
                    }

                    formatted_prompt = prompts[0].format(**context)

                    with details:
                        st.text("Prompt:")
                        st.code(formatted_prompt, language="markdown")

                    with st.spinner("Analyzing threat intelligence..."):
                        result = process_with_llm(formatted_prompt, model, max_tokens, temperature)

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
                        current_detection = {"name": "", "behavior": "", "log_evidence": "", "context": ""}
                        capturing_threat_behavior = False
                        capturing_log_evidence = False
                        capturing_context = False

                        for line in st.session_state.result.split('\n'):
                            stripped_line = line.strip()
                            if stripped_line.startswith(("Detection Name:", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
                                if current_detection["name"]:
                                    detections.append(current_detection)
                                    current_detection = {"name": "", "behavior": "", "log_evidence": "", "context": ""}
                                name = stripped_line.split(":", 1)[-1].strip() if ":" in stripped_line else stripped_line.split(".", 1)[-1].strip()
                                name = name.lstrip("0123456789. ")
                                current_detection["name"] = name
                            elif "Threat Behavior:" in stripped_line:
                                capturing_threat_behavior = True
                                capturing_log_evidence = False
                                capturing_context = False
                                current_detection["behavior"] = stripped_line.split("Threat Behavior:", 1)[-1].strip()
                            elif "Log Evidence:" in stripped_line:
                                capturing_threat_behavior = False
                                capturing_log_evidence = True
                                capturing_context = False
                                current_detection["log_evidence"] = stripped_line.split("Log Evidence:", 1)[-1].strip()
                            elif "Context:" in stripped_line:
                                capturing_threat_behavior = False
                                capturing_log_evidence = False
                                capturing_context = True
                                current_detection["context"] = stripped_line.split("Context:", 1)[-1].strip()
                            elif capturing_threat_behavior:
                                current_detection["behavior"] += " " + stripped_line
                            elif capturing_log_evidence:
                                current_detection["log_evidence"] += " " + stripped_line
                            elif capturing_context:
                                current_detection["context"] += " " + stripped_line

                        if current_detection["name"]:
                            detections.append(current_detection)

                        if not detections:
                            st.warning("No specific detections were identified. The entire analysis will be processed as a single detection.")
                            detections = [{"name": "Entire Analysis", "behavior": st.session_state.result, "log_evidence": "", "context": ""}]

                        st.session_state.detections = detections

                    # Display the number of detections found
                    st.info(f"Number of detections found: {len(detections)}")

                    # Display the names of the detections and their threat behaviors
                    if detections:
                        st.write("Detections found:")
                        for detection in detections:
                            st.markdown(f"**Detection Name:** {detection['name']}")
                            st.write(f"**Threat Behavior:** {detection['behavior']}")
                            st.write(f"**Log Evidence:** {detection['log_evidence']}")
                            st.write(f"**Context:** {detection['context']}")
                            st.write("---")

                    # Allow user to select a detection
                    selected_detection_name = st.selectbox("Select a detection to process:", [d["name"] for d in st.session_state.detections])

                    if st.button("Process Selected Detection", type="primary"):
                        selected_detection = next(d for d in st.session_state.detections if d["name"] == selected_detection_name)
                        st.session_state.selected_detection = selected_detection
                        st.session_state.step = 2
                        update_progress()

                if st.session_state.step >= 2:
                    # Process the remaining steps for the selected detection
                    selected_detection = st.session_state.selected_detection

                    st.write("Processing the selected detection:")
                    st.markdown(f"**Detection Name:** {selected_detection['name']}")
                    st.write(f"**Threat Behavior:** {selected_detection['behavior']}")
                    st.write(f"**Log Evidence:** {selected_detection['log_evidence']}")
                    st.write(f"**Context:** {selected_detection['context']}")

                    # Further processing steps...
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
                            "previous_analysis": selected_detection,
                            "previous_detection_rule": results.get(2, ""),
                            "previous_investigation_steps": results.get(3, ""),
                            "previous_qa_findings": results.get(4, "")
                        }

                        formatted_prompt = prompts[i-1].format(**context)

                        with details:
                            st.text("Prompt:")
                            st.code(formatted_prompt, language="markdown")

                        with st.spinner(f"Processing {step_name}..."):
                            result = process_with_llm(formatted_prompt, model, max_tokens, temperature)

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
        This feature spins up a crew of autonomous AI agents that perform threat detection research on your topic of choice. They are maxed out at 5 iterations each, so no need to worry
        about them going rogue and taking over the world.

        This feature is currently limited to OpenAI models.
        
        These agents use Exa, which employs semantic search (embeddings) to search the web, providing more contextually relevant results than traditional keyword-based search engines like Google.
        
        **Examples of research topics:**
        - Threat hunting in Okta logs
        - Most common TTPs used by attackers in AWS
        - Latest detection strategies for ransomware in Windows environments
        """)

        # Add the CrewAI model selection here
        crewai_model = st.selectbox(
            "CrewAI Model",
            ["gpt-4o-mini", "gpt-4-turbo", "gpt-4o"],
            index=0,  # Set default to gpt-3.5-turbo
            key="crewai_model",
            help="Select the model for CrewAI to use"
        )

        research_query = st.text_input(
            "Enter your cybersecurity research topic:",
            placeholder="E.g., 'Threat hunting in Okta logs' or 'TTPs from CloudTrail logs used in AWS attacks'",
            help="Specify a topic for in-depth threat research to supplement your analysis."
        )

        if st.button("🔍 Perform Threat Research", type="primary", key="research_button"):
            if research_query:
                with st.spinner("Performing threat research... This may take a few minutes."):
                    research_result = run_threat_research(research_query, crewai_model)
                
                st.subheader("Threat Research Results")
                st.markdown(research_result)
                
            else:
                st.warning("Please enter a research topic before performing threat research.")
    with tab3:
        st.subheader("Open Source Detection Content")
        
        st.markdown("[![Elastic](https://img.shields.io/badge/Elastic-005571?style=for-the-badge&logo=elastic&logoColor=white)](https://github.com/elastic/detection-rules)")
        st.markdown("[![Chronicle](https://img.shields.io/badge/Chronicle-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://github.com/chronicle/detection-rules)")
        st.markdown("[![Sigma](https://img.shields.io/badge/Sigma-008080?style=for-the-badge&logo=sigma&logoColor=white)](https://github.com/SigmaHQ/sigma)")
        st.markdown("[![Hacking the Cloud](https://img.shields.io/badge/Hacking_the_Cloud-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://hackingthe.cloud/)")
        st.markdown("[![Wiz Threats](https://img.shields.io/badge/Wiz_Threats-00ADEF?style=for-the-badge&logo=wiz&logoColor=white)](https://threats.wiz.io/)")
        st.markdown("[![Anvilogic Armory](https://img.shields.io/badge/Anvilogic_Armory-6F2DA8?style=for-the-badge&logo=github&logoColor=white)](https://github.com/anvilogic-forge/armory)")
        st.markdown("[![Panther](https://img.shields.io/badge/Panther-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/panther-labs/panther-analysis/tree/release/rules)")
        st.markdown("[![Splunk](https://img.shields.io/badge/Splunk-000000?style=for-the-badge&logo=splunk&logoColor=white)](https://github.com/splunk/security_content)")
        st.markdown("[![Datadog](https://img.shields.io/badge/Datadog-632CA6?style=for-the-badge&logo=datadog&logoColor=white)](https://docs.datadoghq.com/security/default_rules/)")
        st.markdown("[![Falco Security](https://img.shields.io/badge/Falco_Security-6A737D?style=for-the-badge&logo=github&logoColor=white)](https://github.com/falcosecurity/rules)")
        st.markdown("[![ExaBeam Content Library](https://img.shields.io/badge/ExaBeam-008080?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ExabeamLabs/Content-Doc)")
        st.markdown("[![Sekoia Detection Rules](https://img.shields.io/badge/Sekoia_Detection-0000FF?style=for-the-badge&logo=github&logoColor=white)](https://docs.sekoia.io/xdr/features/detect/built_in_detection_rules/)")
        st.markdown("[![Sublime](https://img.shields.io/badge/Sublime-FF6347?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sublime-security/sublime-rules/)")
        st.markdown("[![Cloud Security Atlas](https://img.shields.io/badge/Cloud_Security_Atlas-632CA6?style=for-the-badge&logo=datadog&logoColor=white)](https://securitylabs.datadoghq.com/cloud-security-atlas/)")
        st.markdown("[![SaaS Attack Matrix](https://img.shields.io/badge/SaaS_Attack_Matrix-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pushsecurity/saas-attacks)")
        st.markdown("[![Delivr.to Email Detections](https://img.shields.io/badge/Delivr.to-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/delivr-to/detections)")
        st.markdown("[![Public Cloud Breaches](https://img.shields.io/badge/Public_Cloud_Breaches-FF5733?style=for-the-badge&logo=google-cloud&logoColor=white)](https://www.breaches.cloud/)")
        st.markdown("[![CI/CD Threat Matrix](https://img.shields.io/badge/CI/CD_Threat_Matrix-6A737D?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rung/threat-matrix-cicd)")
        st.markdown("[![K8s Attack Trees](https://img.shields.io/badge/K8s_Attack_Trees-0000FF?style=for-the-badge&logo=kubernetes&logoColor=white)](https://github.com/cncf/financial-user-group/tree/main/projects/k8s-threat-model)")
        st.markdown("[![eBPF Detections](https://img.shields.io/badge/eBPF_Detections-005571?style=for-the-badge&logo=aqua&logoColor=white)](https://github.com/aquasecurity/tracee/tree/main/signatures/golang)")
        st.markdown("[![Insider Threat TTP KnowledgeBase](https://img.shields.io/badge/Insider_Threat_TTP_KnowledgeBase-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/center-for-threat-informed-defense/insider-threat-ttp-kb)")
        st.markdown("[![Insider Threat Matrix](https://img.shields.io/badge/Insider_Threat_Matrix-FF9900?style=for-the-badge&logo=mitre&logoColor=white)](https://insiderthreatmatrix.org/)")
        st.markdown("[![Mitre Atlas](https://img.shields.io/badge/Mitre_Atlas-FF6347?style=for-the-badge&logo=mitre&logoColor=white)](https://atlas.mitre.org/techniques)")
        st.markdown("[![Dorothy](https://img.shields.io/badge/Dorothy-005571?style=for-the-badge&logo=elastic&logoColor=white)](https://github.com/elastic/dorothy)")
        st.markdown("[![Stratus Red Team](https://img.shields.io/badge/Stratus_Red_Team-000000?style=for-the-badge&logo=redhat&logoColor=white)](https://stratus-red-team.cloud/)")
        st.markdown("[![KubeHound](https://img.shields.io/badge/KubeHound-632CA6?style=for-the-badge&logo=kubernetes&logoColor=white)](https://github.com/DataDog/KubeHound)")
        st.markdown("[![RedKube](https://img.shields.io/badge/RedKube-FF0000?style=for-the-badge&logo=kubernetes&logoColor=white)](https://github.com/lightspin-tech/red-kube)")
        st.markdown("[![Kubesploit](https://img.shields.io/badge/Kubesploit-6A737D?style=for-the-badge&logo=kubernetes&logoColor=white)](https://github.com/cyberark/kubesploit)")
        st.markdown("[![Kubehunter](https://img.shields.io/badge/Kubehunter-005571?style=for-the-badge&logo=kubernetes&logoColor=white)](https://github.com/aquasecurity/kube-hunter)")
        st.markdown("[![Workload Security Evaluator](https://img.shields.io/badge/Workload_Security_Evaluator-632CA6?style=for-the-badge&logo=datadog&logoColor=white)](https://github.com/DataDog/workload-security-evaluator)")
        st.markdown("[![DeRF](https://img.shields.io/badge/DeRF-6A737D?style=for-the-badge&logo=github&logoColor=white)](https://github.com/vectra-ai-research/derf)")
        st.markdown("[![AWS Threat Composer](https://img.shields.io/badge/AWS_Threat_Composer-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://github.com/awslabs/threat-composer)")


    st.markdown("---")
