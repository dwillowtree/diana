# DIANA: Detection and Intelligence Analysis for New Alerts

Diana is a Streamlit application that processes cybersecurity threat intelligence and generates high-quality detection logic, investigation steps, and response procedures using Large Language Models (LLMs).

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/dwillowtree/diana.git
   cd diana
   ```
2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   pip install 'crewai[tools]' # you will need to manually install this library
   ```
4. Set up your environment variables:
   - Copy the `.env.example` file to `.env`
   - Edit the `.env` file and add your OpenAI, Anthropic, and EXA AI API keys

## Usage

To run the Streamlit app locally:
```
streamlit run app.py
```
Then, open your web browser and go to `http://localhost:8501`.

## Configuration

1. Obtain API keys:
   - For OpenAI: Visit https://platform.openai.com/account/api-keys
   - For Anthropic: Visit https://www.anthropic.com or follow their documentation
   - For EXA AI: Visit https://exa.ai to obtain your API key

2. Add your API keys to the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   EXA_API_KEY=your_exa_ai_api_key_here
   ```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature-name`)
6. Create a new Pull Request

Please ensure that your code follows the existing style and includes appropriate tests and documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.