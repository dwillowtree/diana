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