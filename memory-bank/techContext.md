# Technical Context: RAG Assistant Interface

## Technologies Used

### Backend
- **Python**: Primary programming language for the backend
- **Flask**: Web framework for the API
- **OpenAI Python SDK**: For interacting with Azure OpenAI services
- **Azure SDK for Python**: For interacting with Azure Cognitive Search
- **python-dotenv**: For loading environment variables from .env files
- **logging**: For application logging

### Frontend
- **HTML/CSS/JavaScript**: For the user interface
- **Fetch API**: For making API calls to the backend
- **JSON**: For data exchange between frontend and backend

### Azure Services
- **Azure OpenAI**: For generating embeddings and text completions
- **Azure Cognitive Search**: For storing and retrieving knowledge base content

## Development Setup

### Local Development
1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.template` to `.env` and configure environment variables
6. Run the application: `python app.py`

### Environment Variables
The application uses the following environment variables:

#### Azure OpenAI Configuration
- `OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `OPENAI_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_API_KEY`: Alternative name for Azure OpenAI API key
- `OPENAI_API_VERSION`: Azure OpenAI API version
- `EMBEDDING_DEPLOYMENT`: Azure OpenAI deployment name for embeddings
- `CHAT_DEPLOYMENT`: Azure OpenAI deployment name for chat completions

#### Azure Cognitive Search Configuration
- `SEARCH_ENDPOINT`: Azure Cognitive Search endpoint
- `SEARCH_INDEX`: Azure Cognitive Search index name
- `SEARCH_KEY`: Azure Cognitive Search API key
- `VECTOR_FIELD`: Field name for vector embeddings in the search index

#### Application Settings
- `FEEDBACK_DIR`: Directory for storing feedback data
- `FLASK_ENV`: Flask environment (development/production)
- `PORT`: Port for the Flask application
- `LOG_FORMAT`: Format for log messages
- `LOG_FILE`: File for logging
- `LOG_LEVEL`: Logging level

## Technical Constraints

### Azure OpenAI
- Requires valid Azure OpenAI deployments for embeddings and chat completions
- API rate limits may apply depending on the Azure OpenAI tier
- Token limits apply to both input and output

### Azure Cognitive Search
- Requires a properly configured search index with vector search capabilities
- Search index must contain the specified vector field
- API rate limits may apply depending on the Azure Cognitive Search tier

### Application
- Single-threaded Flask server may limit concurrent requests
- Response time depends on Azure OpenAI and Azure Cognitive Search performance
- Memory usage may increase with large context windows or high concurrency

## Dependencies

### Direct Dependencies
- `flask`: Web framework
- `openai`: OpenAI API client
- `azure-search-documents`: Azure Cognitive Search client
- `azure-core`: Azure core functionality
- `python-dotenv`: Environment variable management
- `requests`: HTTP client
- `logging`: Logging functionality

### Indirect Dependencies
- `jinja2`: Template engine used by Flask
- `werkzeug`: WSGI utility library used by Flask
- `itsdangerous`: Security-related helpers used by Flask
- `click`: Command-line interface creation kit used by Flask
- `markupsafe`: String handling for HTML/XML used by Jinja2

## Tool Usage Patterns

### Environment Configuration
```python
from dotenv import load_dotenv
load_dotenv(override=True)

import os
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
```

### Azure OpenAI Client Initialization
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version,
)
```

### Azure Cognitive Search Client Initialization
```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

client = SearchClient(
    endpoint=f"https://{search_endpoint}.search.windows.net",
    index_name=search_index,
    credential=AzureKeyCredential(search_key),
)
```

### Vector Search Query
```python
from azure.search.documents.models import VectorizedQuery

vec_q = VectorizedQuery(
    vector=embedding,
    k_nearest_neighbors=10,
    fields="vector_field",
)
results = client.search(
    search_text=query,
    vector_queries=[vec_q],
    select=["chunk", "title"],
    top=10,
)
```

### OpenAI Chat Completion
```python
response = client.chat.completions.create(
    model=deployment_name,
    messages=messages,
    max_tokens=max_tokens,
    temperature=temperature,
)
