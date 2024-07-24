# firecrawl_integration.py
import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Firecrawl API key from the .env file
API_KEY = os.getenv('FIRECRAWL_API_KEY')

def scrape_url(url):
    app = FirecrawlApp(api_key=API_KEY)
    response = app.scrape_url(url=url)
    print(response)  # Debugging output to check the response structure
    if isinstance(response, dict) and 'success' in response and response['success']:
        return response['data']['markdown']
    elif isinstance(response, dict) and 'content' in response:
        return response['content']  # Fallback to returning the 'content' key if the structure is different
    else:
        raise Exception(f"Error scraping URL: {response}")


