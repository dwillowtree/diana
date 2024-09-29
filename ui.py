# ui.py

import streamlit as st
from app import process_threat_intel
from utils.logging_config import logger, log_user_action, log_error
from utils.github import sync_to_github, test_github_connection
from database import get_all_raw_intel, get_all_processed_intel, get_all_detections

def render_ui():
    st.set_page_config(page_title="D.I.A.N.A.", page_icon="🛡️", layout="wide")
    st.title("🛡️ D.I.A.N.A.")
    st.subheader("Detection and Intelligence Analysis for New Alerts")

    # Sidebar
    with st.sidebar:
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

        # Configuration
        st.subheader("Configuration")
        llm_provider = st.selectbox(
            "LLM Provider",
            ["OpenAI", "Anthropic", "Amazon Bedrock", "Groq"],
            index=1,
            key="llm_provider",
            help="Choose the AI model provider for processing."
        )
        log_user_action(f"Selected LLM Provider: {llm_provider}")

        model = st.selectbox(
            "Model Type",
            ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            index=2, 
            key="model",
            help="Select the model to use for processing."
        )
        log_user_action(f"Selected Model Type: {model}")

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.1,
            key="temperature_slider",
            help="Controls output randomness. Lower values for more deterministic results, higher values for more creative outputs."
        )
        log_user_action(f"Set Temperature: {temperature}")
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=4000,
            step=100,
            key="max_tokens_slider",
            help="Maximum number of tokens in the generated response."
        )
        log_user_action(f"Set Max Tokens: {max_tokens}")

    # Main content
    tab1, tab2, tab3 = st.tabs(["Threat Intel Analysis", "GitHub Sync", "Debug Info"])

    with tab1:
        render_threat_intel_tab(model, max_tokens, temperature)

    with tab2:
        render_github_sync_tab()

    with tab3:
        render_debug_tab()

def render_threat_intel_tab(model, max_tokens, temperature):
    st.header("Threat Intelligence Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        description = st.text_area(
            "Enter threat intelligence description:",
            height=150,
            help="Provide a detailed description of the threat intelligence you want to analyze.",
            placeholder="E.g., A new ransomware strain has been observed targeting healthcare organizations. The malware encrypts files with a .locked extension and drops a ransom note named README.txt in each directory."
        )
        uploaded_file = st.file_uploader(
            "Upload threat intel report or blog (optional)",
            type=["txt", "pdf"],
            help="You can optionally upload a threat intelligence report or blog post for analysis."
        )
        if uploaded_file:
            log_user_action(f"Uploaded file: {uploaded_file.name}")

        data_types = st.multiselect(
            "Security Data/Log Type(s)",
            ["Okta Logs", "AWS CloudTrail Logs", "Kubernetes Audit Logs", "GitLab Audit Logs", "AWS EKS Plane logs", "Cisco Duo Logs"],
            default=["AWS CloudTrail Logs"],
            key="security_data_type",
            help="Select the relevant log types for your detection."
        )
        log_user_action(f"Selected Data Types: {', '.join(data_types)}")

        detection_language = st.selectbox(
            "Detection Language",
            [
                "AWS Athena", "StreamAlert", "Splunk SPL", "Falcon LogScale", "Elastic Query DSL",
                "Kusto Query Language (KQL)", "Sigma Rules", "Panther (Python)", "Hunters (Snowflake SQL)"
            ],
            key="detection_language_select",
            help="Choose the query language for your detection rules."
        )
        log_user_action(f"Selected Detection Language: {detection_language}")

    with col2:
        st.subheader("Example Detections")
        num_detections = st.number_input("Number of example detections", min_value=1, value=2, step=1)
        current_detections = [
            st.text_area(
                f"Example detection {i+1}",
                height=100,
                key=f"detection_{i}",
                help="Provide an example of an existing detection query in your environment.",
                placeholder=f"E.g., Detection {i+1}:\nSELECT * FROM cloudtrail_logs\nWHERE eventName = 'CreateUser'\nAND userIdentity.type != 'IAMUser'\nAND userIdentity.invokedBy NOT LIKE 'AWS%'"
            ) for i in range(num_detections)
        ]
        log_user_action(f"Provided {num_detections} example detections")
        
        st.subheader("Example Logs")
        num_logs = st.number_input("Number of example logs", min_value=1, value=2, step=1)
        example_logs = [
            st.text_area(
                f"Example log {i+1}",
                height=100,
                key=f"log_{i}",
                help="Provide examples of actual log entries from your environment.",
                placeholder=f"E.g., Log {i+1}:\n{{'eventVersion': '1.08', 'eventName': 'CreateUser', 'eventTime': '2024-09-28T18:30:00Z', 'userIdentity': {{'type': 'Root', 'principalId': 'AIDACKCEVSQ6C2EXAMPLE'}}, 'eventSource': 'iam.amazonaws.com'}}"
            ) for i in range(num_logs)
        ]
        log_user_action(f"Provided {num_logs} example logs")

    with st.expander("Detection Writing Steps", expanded=False):
        detection_steps = st.text_area(
            "Enter detection writing steps:",
            height=150,
            help="Outline the steps you typically follow when writing detection rules.",
            placeholder="1. Identify the key indicators or behaviors from the threat intel\n2. Determine the relevant log sources and fields\n3. Write the query using the specified detection language\n4. Include appropriate filtering to reduce false positives\n5. Add comments to explain the logic of the detection"
        )

    with st.expander("Alert Triage Steps", expanded=False):
        sop = st.text_area(
            "Enter standard operating procedures or investigation steps for your current detections and alerts:",
            height=150,
            help="Describe your standard operating procedures for triaging and investigating alerts.",
            placeholder="1. Verify the alert details and affected resources\n2. Check for any related alerts or suspicious activity\n3. Analyze the relevant logs and timeline of events\n4. Determine the potential impact and scope of the threat\n5. Initiate containment measures if a threat is confirmed\n6. Document findings and update the detection if necessary"
        )

    if st.button("🚀 Process Threat Intel", type="primary"):
        log_user_action("Clicked 'Process Threat Intel' button")
        with st.spinner("Processing threat intelligence..."):
            try:
                file_content = uploaded_file.read() if uploaded_file else None
                result = process_threat_intel(
                    description=description,
                    file_content=file_content,
                    model=model,
                    data_types=data_types,
                    detection_language=detection_language,
                    current_detections=current_detections,
                    example_logs=example_logs,
                    detection_steps=detection_steps,
                    sop=sop,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                if result:
                    st.success("Processing complete!")
                    st.subheader("Detection Results")
                    st.write(f"**Detection Name:** {result['detection_name']}")
                    st.write(f"**Threat Description:** {result['threat_description']}")
                    st.write("**Detection Rule:**")
                    st.code(result['detection_rule'], language=detection_language.lower())
                    st.write(f"**Log Sources:** {result['log_sources']}")
                    st.write("**Investigation Steps:**")
                    st.write(result['investigation_steps'])
                    st.write(f"**QA Score:** {result['qa_score']}/100")
                    st.write(f"**QA Summary:** {result['qa_summary']}")
                    st.write(f"**Processing Time:** {result['processing_time']:.2f} seconds")
                    log_user_action("Successfully processed threat intel")
                    
                    # Store the result in session state for use in GitHub sync
                    st.session_state.last_processed_result = result
                else:
                    st.error("An error occurred during processing. Please check the logs for more information.")
                    log_error("Processing threat intel returned None")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                log_error(f"Error in UI while processing threat intel: {str(e)}", exc_info=True)

def render_github_sync_tab():
    st.header("GitHub Sync")
    
    if 'last_processed_result' in st.session_state:
        result = st.session_state.last_processed_result
        st.write(f"Last processed detection: {result['detection_name']}")
        
        if st.button("Sync to GitHub"):
            log_user_action("User clicked 'Sync to GitHub' button")
            try:
                with st.spinner("Syncing to GitHub..."):
                    sync_success, sync_message = sync_to_github(
                        result['detection_name'],
                        result['detection_rule'],
                        result['threat_description']
                    )
                    if sync_success:
                        st.success(sync_message)
                        log_user_action(f"Successfully synced to GitHub: {result['detection_name']}")
                    else:
                        st.error(f"Failed to sync to GitHub: {sync_message}")
                        log_error(f"GitHub sync failed: {sync_message}")
            except Exception as e:
                st.error(f"An unexpected error occurred during GitHub sync: {str(e)}")
                log_error(f"Unexpected error in GitHub sync: {str(e)}", exc_info=True)
    else:
        st.info("No processed threat intel available for sync. Please process threat intel first.")

    if st.button("Test GitHub Connection"):
        log_user_action("User clicked 'Test GitHub Connection' button")
        try:
            repo_name = test_github_connection()
            st.success(f"Successfully connected to GitHub repo: {repo_name}")
            log_user_action(f"Successfully tested GitHub connection to repo: {repo_name}")
        except Exception as e:
            st.error(f"Failed to connect to GitHub: {str(e)}")
            log_error(f"GitHub connection test failed: {str(e)}", exc_info=True)

def render_debug_tab():
    st.header("Debug Information")
    
    if st.checkbox("Show Database Contents"):
        st.subheader("Raw Intel")
        raw_intel = get_all_raw_intel()
        st.write(raw_intel)

        st.subheader("Processed Intel")
        processed_intel = get_all_processed_intel()
        st.write(processed_intel)

        st.subheader("Detections")
        detections = get_all_detections()
        st.write(detections)
    
    if 'last_processed_result' in st.session_state:
        st.subheader("Last Processed Result")
        st.json(st.session_state.last_processed_result)
    else:
        st.info("No processed result available.")

if __name__ == "__main__":
    logger.info("Starting DIANA UI")
    render_ui()
    logger.info("DIANA UI stopped")