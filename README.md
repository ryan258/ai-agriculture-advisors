# AI Agriculture Advisors

AI Agriculture Advisors is a Node.js application that leverages a local Large Language Model (LLM) to provide expert advice on various aspects of agriculture. The system simulates a team of AI-driven agricultural experts, each specializing in different areas of the agricultural sector.

## Features

- Five AI expert roles:
  - Agricultural Science Expert
  - Climate Change Impact Analyst
  - Commodities Trading Specialist
  - AgriTech Innovation Researcher
  - Food Supply Chain Analyst
- Web interface for easy interaction with AI experts
- Markdown rendering for formatted responses
- Logging system to track all interactions

## Prerequisites

- Node.js (v14 or later recommended)
- npm (comes with Node.js)
- A local LLM setup (e.g., Ollama running llama3.1:latest)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-agriculture-advisors.git
   cd ai-agriculture-advisors
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Make sure your local LLM (Ollama) is running and accessible at `http://localhost:11434`.

## Configuration

- The application uses environment variables for configuration. Create a `.env` file in the root directory with the following content:
  ```
  PORT=3000
  LLM_API_URL=http://localhost:11434/api/generate
  LLM_MODEL_NAME=llama3.1:latest
  ```

## Usage

1. Start the server:
   ```
   npm start
   ```

2. Open a web browser and navigate to `http://localhost:3000` (or the port you specified in the .env file).

3. Select an expert, enter your query, and click "Submit Query" to get a response.

## Project Structure

```
ai-agriculture-advisors/
├── src/
│   ├── server.js
│   ├── routes/
│   │   └── api.js
│   ├── controllers/
│   │   ├── agricultureExpert.js
│   │   ├── climateAnalyst.js
│   │   ├── commoditiesSpecialist.js
│   │   ├── agritechResearcher.js
│   │   └── supplyChainAnalyst.js
│   ├── services/
│   │   └── llamaService.js
│   └── utils/
│       └── logger.js
├── public/
│   └── index.html
├── agri-ai.txt
├── package.json
├── .env
└── README.md
```

## Logging

All interactions with the AI experts are logged in the `agri-ai.txt` file, located in the project root directory. Each log entry includes the timestamp, expert role, query, and response.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses [Ollama](https://ollama.ai/) for local LLM integration.
- Markdown rendering is done using the [marked](https://marked.js.org/) library.