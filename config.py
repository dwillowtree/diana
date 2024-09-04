# Prompts for each step of the process
prompts = [
    # Prompt 1: Analyze threat intelligence
    """You are an expert cyber security threat intelligence analyst. 
    The intel will be provided to you in the form of incident reports, threat intel reports, cyber security blogs, adverary emulation tools, existing detection content, or any description in natural language
    of techniques, tactics and procedures (TTPs) used by cyber security threat actors. Avoid using atomic indicators like IP addresses or domain names. Focus only on behaviors or techniques.
    Analyze the following threat intelligence:

Description: {description}
Blog/Report (if provided): {file_content}
Scraped Website Content (if provided): {scraped_content}

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
    """As a QA specialist in cyber threat detection with extensive experience in {detection_language}, conduct a thorough and comprehensive review of the following detection rule:

Detection Rule:
{previous_detection_rule}

Analysis from Threat Intelligence:
{previous_analysis}

Assess the following aspects in detail, providing a score out of 10 for each:

1. Syntactic Correctness (10 points):
   - Is the rule syntactically correct in {detection_language}?
   - Are there any syntax errors or potential runtime issues?
   - Does it follow best practices and conventions for {detection_language}?

2. Logical Accuracy (10 points):
   - Does the rule accurately capture all aspects of the threat behavior described in the analysis?
   - Are there any logical errors or misinterpretations of the threat intelligence?
   - Is the detection logic complete and comprehensive?

3. Coverage (10 points):
   - Does the rule cover all potential variations of the threat behavior?
   - Are there any edge cases or scenarios not addressed by the current implementation?

4. Performance and Efficiency (10 points):
   - Is the detection optimized for performance in the target environment?
   - Are there any potential bottlenecks or resource-intensive operations?
   - Could the rule be optimized without sacrificing accuracy?

5. False Positive/Negative Analysis (10 points):
   - Provide a realistic estimate of both false positive and false negative rates
   - Justify your estimates with specific scenarios or data points
   - Suggest ways to minimize false positives without increasing false negatives

6. Robustness and Evasion Resistance (10 points):
   - How easily could an attacker evade this detection?
   - Are there any obvious bypass methods?
   - Suggest improvements to make the detection more robust against evasion techniques

7. Investigation Guide Quality (10 points):
   - Are the investigation steps clear, comprehensive, and actionable?
   - Do they cover all necessary aspects of validation, investigation, and response?
   - Are there any missing steps or areas that need more detail?

8. Integration and Dependencies (10 points):
   - Does the rule rely on any external data sources or lookups?
   - Are there any potential issues with data availability or freshness?

9. Maintenance and Updatability (10 points):
   - How easily can this rule be updated or modified in the future?
   - Are there any hard-coded elements that might require frequent updates?

10. Overall Effectiveness (10 points):
    - How well does the detection rule achieve its intended purpose?
    - Does it strike a good balance between accuracy, performance, and maintainability?

For each aspect, provide:
- A score out of 10
- Detailed explanation of your assessment
- Specific, actionable recommendations for improvement
- If no changes are needed, a thorough justification for why the current version is optimal

Present your QA findings as a structured report with clear recommendations for each aspect. Include code snippets or pseudo-code where applicable to illustrate suggested improvements.

Conclude with an overall assessment of the detection rule's quality and readiness for production deployment, including the total score out of 100 and a brief explanation of the score.""",

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

## Log Sources
[List of specific log sources or data types required for this detection]

##Investigation Steps
[Numbered list of investigation steps from {previous_investigation_steps}]

Performance Considerations
[Brief notes on expected performance, including estimated false positive rate]

## Quality Assessment
[Give the overall score out of 100 and the summary from {previous_qa_findings}]

Ensure the final output is well-structured, comprehensive, and ready for review and implementation by the security operations team."""

]