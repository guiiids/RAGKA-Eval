# RAG Assistant Interface

A modern web interface for interacting with your RAG (Retrieval-Augmented Generation) assistant powered by Azure OpenAI.

## Features

- **3-Card Layout Interface**:
  - **Card 1**: Model Parameters - Configure GPT mode, prompt, temperature, top-k, and top-p
  - **Card 2**: Model Output - Display responses, sources, and metadata
  - **Card 3**: AI Evaluation - Real-time evaluation of response quality

- **Azure OpenAI Integration**: Seamlessly connects to your Azure OpenAI deployment
- **Environment Configuration**: Uses .env files for secure configuration management
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Evaluation**: Provides quality metrics for generated responses

## Setup Instructions

### 1. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp .env.template .env
```

Edit the `.env` file with your actual Azure OpenAI and Azure Cognitive Search credentials:

```env
# Azure OpenAI Configuration
OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
OPENAI_KEY=your-azure-openai-api-key
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
OPENAI_API_VERSION=2024-02-15-preview

# Azure OpenAI Deployment Names
EMBEDDING_DEPLOYMENT=text-embedding-ada-002
CHAT_DEPLOYMENT=gpt-4

# Azure Cognitive Search Configuration
SEARCH_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_INDEX=your-search-index-name
SEARCH_KEY=your-search-admin-key
VECTOR_FIELD=content_vector
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5001`


**Production Mode**: To use real Azure OpenAI functionality:
1. Set `DEMO_MODE=false` in your `.env` file
2. Configure all Azure OpenAI and Cognitive Search credentials
3. Restart the application

## File Structure

```
rag_interface/
├── app.py                 # Flask backend application
├── index.html            # Main interface with 3 cards
├── config.py             # Configuration management
├── rag_assistant.py      # RAG assistant implementation
├── llm_summary.py        # LLM evaluation utilities
├── main.py               # Original main application
├── .env.template         # Environment variables template
└── README.md            # This file
```

## API Endpoints

- `GET /` - Serves the main interface
- `POST /api/query` - Process queries and return responses
- `POST /api/evaluate` - Evaluate response quality
- `GET /api/health` - Health check endpoint

## Usage

1. **Configure Parameters**: Use Card 1 to set your GPT model, prompt, and generation parameters
2. **Generate Response**: Click "Generate Response" to query your RAG assistant
3. **View Results**: Card 2 displays the response, sources, and metadata
4. **Review Evaluation**: Card 3 shows quality metrics and suggestions for improvement

## Customization

- Modify `index.html` to customize the interface design
- Update `app.py` to add new API endpoints or modify existing functionality
- Extend `rag_assistant.py` to integrate with different knowledge bases or models

## Troubleshooting

- Check the console logs for any JavaScript errors
- Verify your `.env` file contains all required variables
- Ensure your Azure OpenAI and Cognitive Search services are properly configured
- Check the Flask application logs for backend errors

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables for all sensitive configuration
- Implement proper authentication for production deployments

