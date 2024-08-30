# agents/tools/splunk_search_tool.py
from crewai_tools import BaseTool
import requests

class SplunkSearchTool(BaseTool):
    name: str = "SplunkSearchTool"
    description: str = "This tool allows the agent to perform searches on a Splunk instance via the REST API."

    def __init__(self, splunk_base_url: str, auth_token: str):
        self.splunk_base_url = splunk_base_url
        self.auth_token = auth_token

    def _run(self, search_query: str) -> str:
        # Step 1: Create a search job in Splunk
        search_job_id = self._create_search_job(search_query)
        if not search_job_id:
            return "Failed to create search job."

        # Step 2: Poll the search job until it's done
        if not self._wait_for_search_completion(search_job_id):
            return "Search job failed or was canceled."

        # Step 3: Retrieve the results
        results = self._get_search_results(search_job_id)
        if not results:
            return "Failed to retrieve search results."

        return results

    def _create_search_job(self, search_query: str) -> str:
        url = f"{self.splunk_base_url}/services/search/jobs"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        data = {
            "search": search_query,
            "output_mode": "json"
        }
        response = requests.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 201:
            return response.json().get("sid")
        else:
            print(f"Error creating search job: {response.text}")
            return None

    def _wait_for_search_completion(self, search_job_id: str) -> bool:
        url = f"{self.splunk_base_url}/services/search/jobs/{search_job_id}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }

        while True:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                content = response.json()
                dispatch_state = content.get("entry")[0].get("content").get("dispatchState")
                if dispatch_state == "DONE":
                    return True
                elif dispatch_state in ["FAILED", "CANCELED"]:
                    return False
            else:
                print(f"Error checking search job status: {response.text}")
                return False

    def _get_search_results(self, search_job_id: str) -> str:
        url = f"{self.splunk_base_url}/services/search/jobs/{search_job_id}/results"
        headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
        params = {
            "output_mode": "json"
        }

        response = requests.get(url, headers=headers, params=params, verify=False)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error retrieving search results: {response.text}")
            return None
