from crewai_tools import BaseTool
from pydantic import Field
import requests
import json
import time
from typing import Dict, Any, Optional
import logging

class SplunkSearchTool(BaseTool):
    name: str = "SplunkSearchTool"
    description: str = "Performs searches on a Splunk instance via the REST API."
    splunk_base_url: str = Field(..., description="The base URL for the Splunk instance")
    auth_token: str = Field(..., description="The authentication token for Splunk API access")
    headers: Dict[str, str] = Field(default_factory=dict)s

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, splunk_base_url: str, auth_token: str, **data):
        super().__init__(splunk_base_url=splunk_base_url, auth_token=auth_token, **data)
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def _run(self, search_query: str, earliest_time: Optional[str] = "-24h", latest_time: Optional[str] = "now", max_results: int = 1000, timeout: int = 300) -> str:
        try:
            search_job_id = self._create_search_job(search_query, earliest_time, latest_time)
            if not search_job_id:
                return "Failed to create search job."

            if not self._wait_for_search_completion(search_job_id, timeout):
                return "Search job timed out or was canceled."

            results = self._get_search_results(search_job_id, max_results)
            if not results:
                return "Failed to retrieve search results or results were empty."

            summary = self._summarize_results(results)
            return summary

        except Exception as e:
            logging.error(f"An error occurred while executing the Splunk search: {str(e)}")
            return f"An error occurred while executing the Splunk search: {str(e)}"

    def _create_search_job(self, search_query: str, earliest_time: str, latest_time: str) -> Optional[str]:
        url = f"{self.splunk_base_url}/services/search/v2/jobs"
        data = {
            "search": search_query,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "output_mode": "json"
        }
        try:
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            return response.json().get("sid")
        except requests.RequestException as e:
            logging.error(f"Error creating search job: {str(e)}")
            logging.error(f"Response content: {e.response.content if e.response else 'No response'}")
            return None

    def _wait_for_search_completion(self, search_job_id: str, timeout: int) -> bool:
        url = f"{self.splunk_base_url}/services/search/jobs/{search_job_id}"
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=headers, verify=False)
                response.raise_for_status()
                content = response.json()
                dispatch_state = content.get("entry")[0].get("content").get("dispatchState")
                
                if dispatch_state == "DONE":
                    return True
                elif dispatch_state in ["FAILED", "CANCELED"]:
                    return False
                
                time.sleep(5)  # Wait before checking again
            except requests.RequestException as e:
                print(f"Error checking search job status: {str(e)}")
                return False

        return False  # Timeout reached

    def _get_search_results(self, search_job_id: str, max_results: int) -> Optional[Dict[str, Any]]:
        url = f"{self.splunk_base_url}/services/search/jobs/{search_job_id}/results"
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        params = {
            "output_mode": "json",
            "count": max_results
        }

        try:
            response = requests.get(url, headers=headers, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error retrieving search results: {str(e)}")
            return None

    def _summarize_results(self, results: Dict[str, Any]) -> str:
        total_results = len(results.get("results", []))
        fields = results.get("fields", [])
        
        summary = f"Total results: {total_results}\n"
        summary += f"Fields: {', '.join(fields)}\n\n"

        if total_results > 0:
            summary += "Sample of results:\n"
            for i, result in enumerate(results.get("results", [])[:5]):  # Show first 5 results
                summary += f"Result {i+1}:\n"
                for field, value in result.items():
                    summary += f"  {field}: {value}\n"
                summary += "\n"

        return summary

# Usage example remains the same