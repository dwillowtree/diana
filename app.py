import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from threat_research import perform_threat_research
from ui import render_ui
from config import prompts

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
            "previous_analysis": results.get(1, "") if "Entire Analysis" in st.session_state.selected_detection else next((d for d in st.session_state.detections if st.session_state.selected_detection in d['name']), ""),            "previous_detection_rule": results.get(2, ""),
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

if __name__ == "__main__":
    render_ui(prompts, process_with_openai, process_with_anthropic)
