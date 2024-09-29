# app.py

import streamlit as st
import os
from dotenv import load_dotenv
from litellm import completion
import litellm
from threat_research import perform_threat_research
from utils.logging_config import logger, log_error
from database import (
    store_detection, get_detection, get_all_detections,
    store_raw_intel, store_processed_intel,
    get_all_raw_intel, get_all_processed_intel,
    store_user_input, store_processing_step
)
import time
import re
import tiktoken

# Load environment variables
load_dotenv()

# Feature flag for file logging
LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'

# Initialize session state for cost tracking
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0

# Shared variable for cost tracking
shared_cost = 0

def track_cost_callback(kwargs, completion_response, start_time, end_time):
    global shared_cost
    try:
        response_cost = kwargs.get("response_cost", 0)
        shared_cost += response_cost
        logger.info(f"Streaming response cost: ${response_cost:.6f}")
    except Exception as e:
        logger.error(f"Error tracking cost: {str(e)}")

litellm.success_callback = [track_cost_callback]

def process_with_llm(prompt, model, max_tokens, temperature):
    global shared_cost
    try:
        logger.info(f"Processing with LLM: {model}")
        start_time = time.time()
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"LLM processing time: {processing_time:.2f} seconds")
        
        st.session_state.total_cost += shared_cost
        logger.info(f"Total cost so far: ${st.session_state.total_cost:.6f}")
        shared_cost = 0
        return response.choices[0].message.content.strip()
    except Exception as e:
        log_error(f"Error with LLM API for {model}: {str(e)}")
        return None

def truncate_text(text, max_tokens):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Use this encoding for Anthropic models as well
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])

def summarize_text(text, model, max_tokens):
    summary_prompt = f"Summarize the following text in no more than {max_tokens//2} tokens:\n\n{text}"
    summary = process_with_llm(summary_prompt, model, max_tokens, 0.7)
    return summary

def process_threat_intel(description, file_content, model, data_types, detection_language, 
                         current_detections, example_logs, detection_steps, sop, max_tokens, temperature):
    logger.info("Starting threat intel processing")
    start_time = time.time()
    
    try:
        # Attempt to decode file_content with different encodings
        decoded_file_content = None
        if file_content:
            encodings_to_try = ['utf-8', 'latin-1', 'ascii', 'utf-16']
            for encoding in encodings_to_try:
                try:
                    decoded_file_content = file_content.decode(encoding)
                    logger.info(f"Successfully decoded file content with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if decoded_file_content is None:
                logger.warning("Unable to decode file content with any known encoding. Treating as binary data.")
                decoded_file_content = str(file_content)  # Fallback to string representation of bytes

        # Truncate and summarize inputs if necessary
        max_input_tokens = 150000  # Leave some room for the model's response
        truncated_description = truncate_text(description, max_input_tokens // 4)
        truncated_file_content = truncate_text(decoded_file_content, max_input_tokens // 4) if decoded_file_content else ""
        
        if len(truncated_description) + len(truncated_file_content) > max_input_tokens // 2:
            logger.info("Input too long, summarizing content")
            combined_content = f"{truncated_description}\n\n{truncated_file_content}"
            summarized_content = summarize_text(combined_content, model, max_input_tokens // 2)
        else:
            summarized_content = f"{truncated_description}\n\n{truncated_file_content}"

        # Truncate other inputs
        truncated_detections = truncate_text("\n".join(current_detections), max_input_tokens // 8)
        truncated_logs = truncate_text("\n".join(example_logs), max_input_tokens // 8)
        truncated_steps = truncate_text(detection_steps, max_input_tokens // 16)
        truncated_sop = truncate_text(sop, max_input_tokens // 16)

        # Store user input
        logger.info("Storing user input")
        user_input_id = store_user_input(
            description=description,
            file_content=decoded_file_content,
            model=model,
            data_types=data_types,
            detection_language=detection_language,
            max_tokens=max_tokens,
            temperature=temperature
        )
        logger.info(f"Stored user input with ID: {user_input_id}")

        # Store raw intel
        logger.info("Storing raw intel")
        raw_intel_id = store_raw_intel(content=summarized_content, source="User Input and File Content")
        logger.info(f"Stored raw intel with ID: {raw_intel_id}")
        store_processing_step(user_input_id, "raw_intel_storage", "success", raw_intel_id)

        # Prepare the prompt
        prompt = f"""
        Analyze the following summarized threat intelligence:
        {summarized_content}

        Data Types: {', '.join(data_types)}
        Detection Language: {detection_language}

        Current Detections (truncated):
        {truncated_detections}

        Example Logs (truncated):
        {truncated_logs}

        Detection Steps (truncated):
        {truncated_steps}

        SOP (truncated):
        {truncated_sop}
        
        Provide a detailed analysis and create a detection rule based on this information.
        Include the following sections in your response:
        1. Detection Name
        2. Threat Description
        3. Detection Rule (in {detection_language})
        4. Log Sources
        5. Investigation Steps
        6. QA Score (out of 100)
        7. QA Summary
        """

        # Process with LLM
        logger.info("Processing with LLM")
        processed_result = process_with_llm(prompt, model, max_tokens, temperature)
        if processed_result is None:
            raise Exception("LLM processing failed")
        
        # Store processed intel
        logger.info("Storing processed intel")
        processed_intel_id = store_processed_intel(raw_intel_id=raw_intel_id, analysis=processed_result)
        logger.info(f"Stored processed intel with ID: {processed_intel_id}")
        store_processing_step(user_input_id, "llm_processing", "success", processed_intel_id)

        # Extract detection information
        logger.info("Extracting detection information")
        detection_name = extract_detection_name(processed_result)
        threat_description = extract_threat_description(processed_result)
        detection_rule = extract_detection_rule(processed_result)
        log_sources = extract_log_sources(processed_result)
        investigation_steps = extract_investigation_steps(processed_result)
        qa_score = extract_qa_score(processed_result)
        qa_summary = extract_qa_summary(processed_result)

        # Store final detection
        logger.info("Storing final detection")
        detection_id = store_detection(
            name=detection_name,
            description=threat_description,
            detection_rule=detection_rule,
            log_sources=log_sources,
            investigation_steps=investigation_steps,
            qa_score=qa_score,
            qa_summary=qa_summary
        )
        logger.info(f"Stored final detection with ID: {detection_id}")
        store_processing_step(user_input_id, "detection_storage", "success", detection_id)

        end_time = time.time()
        total_processing_time = end_time - start_time
        logger.info(f"Total processing time: {total_processing_time:.2f} seconds")

        return {
            "detection_id": detection_id,
            "detection_name": detection_name,
            "threat_description": threat_description,
            "detection_rule": detection_rule,
            "log_sources": log_sources,
            "investigation_steps": investigation_steps,
            "qa_score": qa_score,
            "qa_summary": qa_summary,
            "processing_time": total_processing_time
        }

    except Exception as e:
        log_error(f"Error in process_threat_intel: {str(e)}")
        if 'user_input_id' in locals():
            store_processing_step(user_input_id, "process_failure", "failure", str(e))
        return None

def extract_detection_name(text):
    match = re.search(r'Detection Name:?\s*(.*)', text, re.IGNORECASE)
    return match.group(1).strip() if match else "Unnamed Detection"

def extract_threat_description(text):
    match = re.search(r'Threat Description:?\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_detection_rule(text):
    match = re.search(r'Detection Rule:?\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_log_sources(text):
    match = re.search(r'Log Sources:?\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_investigation_steps(text):
    match = re.search(r'Investigation Steps:?\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_qa_score(text):
    match = re.search(r'QA Score:?\s*(\d+)', text, re.IGNORECASE)
    return int(match.group(1)) if match else 0

def extract_qa_summary(text):
    match = re.search(r'QA Summary:?\s*(.*?)(?=\n\d+\.|\Z)', text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

if __name__ == "__main__":
    from ui import render_ui
    logger.info("Starting DIANA application")
    render_ui()
    logger.info("DIANA application stopped")