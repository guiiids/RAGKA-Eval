import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Load environment variables from .env file
# This is useful for local development

# OpenAI Configuration
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("OPENAI_KEY")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

# Azure OpenAI Deployment Names (fallback defaults)
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT")
CHAT_DEPLOYMENT = os.getenv("CHAT_DEPLOYMENT")

# Azure Cognitive Search Configuration
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_INDEX = os.getenv("SEARCH_INDEX")
SEARCH_KEY = os.getenv("SEARCH_KEY")
VECTOR_FIELD = os.getenv("VECTOR_FIELD")

# Logging Configuration
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Feedback Configuration
FEEDBACK_DIR = os.getenv("FEEDBACK_DIR", "feedback_data")
FEEDBACK_FILE = os.getenv("FEEDBACK_FILE", "feedback.json")

# Database Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SSL_MODE = os.getenv("POSTGRES_SSL_MODE", "require")  # Default to 'require' for Render

# Azure per-model configurations
O3_ENDPOINT = os.getenv("O3_ENDPOINT")
O3_KEY = os.getenv("O3_KEY")
O3_API_VERSION = os.getenv("O3_API_VERSION")
O3_DEPLOYMENT_NAME = os.getenv("O3_DEPLOYMENT_NAME")

O4_MINI_ENDPOINT = os.getenv("O4_MINI_ENDPOINT")
O4_MINI_KEY = os.getenv("O4_MINI_KEY")
O4_MINI_API_VERSION = os.getenv("O4_MINI_API_VERSION")
O4_MINI_DEPLOYMENT_NAME = os.getenv("O4_MINI_DEPLOYMENT_NAME")

# GPT-4o Configuration
GPT4O_ENDPOINT = os.getenv("GPT4O_ENDPOINT")
GPT4O_KEY = os.getenv("GPT4O_KEY")
GPT4O_API_VERSION = os.getenv("GPT4O_API_VERSION")
GPT4O_DEPLOYMENT = os.getenv("GPT4O_DEPLOYMENT")

# Mapping from model identifiers to Azure configurations
MODEL_ENDPOINTS = {
    "o3": O3_ENDPOINT,
    "o4-mini": O4_MINI_ENDPOINT,
    "gpt-4o": GPT4O_ENDPOINT
}
MODEL_KEYS = {
    "o3": O3_KEY,
    "o4-mini": O4_MINI_KEY,
    "gpt-4o": GPT4O_KEY
}
MODEL_API_VERSIONS = {
    "o3": O3_API_VERSION,
    "o4-mini": O4_MINI_API_VERSION,
    "gpt-4o": GPT4O_API_VERSION
}
MODEL_DEPLOYMENTS = {
    "o3": O3_DEPLOYMENT_NAME,
    "o4-mini": O4_MINI_DEPLOYMENT_NAME,
    "gpt-4o": GPT4O_DEPLOYMENT
}
