import streamlit as st
import os
from dotenv import load_dotenv
from litellm import completion
import litellm
from threat_research import perform_threat_research
from ui import render_ui
from config import prompts

# Load environment variables
load_dotenv()

# Initialize session state for cost tracking
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0

# Shared variable for cost tracking
shared_cost = 0

# Define the callback function
def track_cost_callback(kwargs, completion_response, start_time, end_time):
    global shared_cost
    try:
        response_cost = kwargs.get("response_cost", 0)
        shared_cost += response_cost
        print(f"Streaming response cost: ${response_cost:.6f}")
    except Exception as e:
        print(f"Error tracking cost: {str(e)}")

# Set the callback
litellm.success_callback = [track_cost_callback]

def process_with_llm(prompt, model, max_tokens, temperature):
    global shared_cost
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        # Update the Streamlit session state in the main thread
        st.session_state.total_cost += shared_cost
        st.info(f"Total cost so far: ${st.session_state.total_cost:.6f}")
        shared_cost = 0  # Reset shared cost after updating session state
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error with LLM API for {model}: {str(e)}")
        return None

def process_threat_intel(description, file_content, model, data_types, detection_language, current_detections, example_logs, detection_steps, sop, max_tokens, temperature):
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
            "previous_analysis": results.get(1, "") if "Entire Analysis" in st.session_state.selected_detection else next((d for d in st.session_state.detections if st.session_state.selected_detection in d['name']), ""),
            "previous_detection_rule": results.get(2, ""),
            "previous_investigation_steps": results.get(3, ""),
            "previous_qa_findings": results.get(4, "")
        }
        
        formatted_prompt = prompt.format(**context)
        
        result = process_with_llm(formatted_prompt, model, max_tokens, temperature)
        
        if result is None:
            return None

        results[i] = result
    
    return results

if __name__ == "__main__":
    render_ui(prompts, process_with_llm)
