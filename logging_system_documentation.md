# RAG Interface Logging System Documentation

## Overview

The RAG Interface implements a comprehensive logging system that captures detailed information about user interactions, system operations, and OpenAI API communications. This documentation provides a complete analysis of how the logging system works, what information it stores, and where it pulls data from.

## Logging Architecture

### Core Components

1. **Python Logging Module**: Standard Python logging framework
2. **Flask Request Logging**: Built-in Flask request/response logging
3. **Custom Application Logging**: Application-specific event logging
4. **OpenAI API Logging**: Detailed API interaction logging

### Configuration

#### Log Configuration (config.py)
```python
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

#### Logging Setup (app.py)
```python
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
```

## Information Captured

### 1. Application Lifecycle Events

**Server Startup/Shutdown:**
- Flask development server warnings
- Server binding information (IP addresses and ports)
- Debugger activation status
- Debugger PIN codes
- File change detection and auto-reloading

**Example:**
```
2025-06-07 08:01:48,135 - INFO - [31m[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.[0m
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5011
 * Running on http://10.252.52.27:5011
```

### 2. HTTP Request/Response Logging

**Request Information:**
- Client IP addresses
- HTTP methods (GET, POST)
- Request paths
- Response status codes
- Timestamps

**Example:**
```
2025-06-07 08:01:50,473 - INFO - 127.0.0.1 - - [07/Jun/2025 08:01:50] "GET / HTTP/1.1" 200 -
```

### 3. Query Processing Events

#### Query Mode Logging (main.py)
```python
logger.info(f"Processing query: {query}...")
logger.info(f"Parameters - Model: {model}, Temp: {temperature}, Top-K: {top_k}, Top-P: {top_p}")
```

**Captured Information:**
- User queries (truncated for privacy)
- Model parameters (temperature, top_p, max_tokens)
- Processing timestamps
- Success/failure status
- Processing duration

**Example:**
```
2025-06-06 10:48:47,885 - INFO - Parameters - Model: gpt-4o, Temp: 0.7, Top-K: 50, Top-P: 0.9
2025-06-06 10:48:53,613 - INFO - Query processed successfully in 5727ms
```

#### Evaluation Mode Logging (main.py)
```python
logger.info(f"Eval mode: Query: '{query}'")
logger.info(f"Eval mode: Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")
logger.info(f"Eval mode: System prompt sent to AzureOpenAI: '{system_prompt}'")
logger.info(f"Eval mode: Answer received: {answer[:100]}...")
logger.info(f"Eval mode: Sources count: {len(sources)}")
```

### 4. OpenAI API Interaction Logging

#### Detailed API Request Logging (rag_assistant.py)
The system captures extensive information about OpenAI API interactions:

**Request Details:**
```python
logger.info("========== OPENAI API REQUEST ==========")
logger.info(f"deployment: {deployment_name}, temp: {self.temperature}, tokens: {self.max_tokens}")
```

**System Prompt Logging:**
```python
logger.info("========== SYSTEM PROMPT ==========")
logger.info(system_prompt)
```

**User Content Logging:**
```python
logger.info("========== USER CONTENT ==========")
logger.info(processed_user)
```

**Messages Array Logging:**
```python
logger.info("========== MESSAGES ARRAY ==========")
for i, message in enumerate(messages, 1):
    logger.info(f"Message {i} - Role: {message['role']}")
    logger.info(f"Content: {message['content']}")
```

**Raw Payload Logging:**
```python
logger.info("========== OPENAI RAW PAYLOAD ==========")
logger.info(json.dumps(payload, indent=2))
```

**Response Logging:**
```python
logger.info("DEBUG - OpenAI response content: %s", answer)
```

### 5. Azure Search Integration Logging

**Embedding Generation:**
- HTTP requests to Azure OpenAI embedding endpoints
- Request/response status codes
- API versions and endpoints used

**Search Operations:**
- Azure Cognitive Search requests
- Search index operations
- Request headers and metadata
- Response status and timing information

**Example:**
```
2025-06-07 08:02:21,005 - INFO - Request URL: 'https://capozzol01searchservice.search.windows.net/indexes('vector-1744312841968-pool8')/docs/search.post.search?api-version=REDACTED'
2025-06-07 08:02:21,571 - INFO - Response status: 200
```

### 6. Error Handling and Debugging

**Error Logging:**
- Exception tracebacks
- API error responses
- Connection failures
- Model parameter validation errors

**Example:**
```
2025-06-06 12:07:42,034 - ERROR - Query mode error: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}
```

## Data Sources

### 1. Flask Application (app.py)
- HTTP request/response logging
- Application startup/shutdown events
- Route handling information

### 2. Main Application Logic (main.py)
- Query processing workflows
- Parameter validation
- Mode switching (query vs evaluation)
- Performance metrics

### 3. RAG Assistant (rag_assistant.py)
- OpenAI API interactions
- System prompt construction
- Context preparation
- Response processing
- Fact-checking operations

### 4. Configuration Management (config.py)
- Environment variable loading
- Model configuration mapping
- Endpoint management

### 5. External Services
- **Azure OpenAI API**: Model interactions, embeddings
- **Azure Cognitive Search**: Vector search operations
- **HTTP Clients**: Request/response metadata

## Log File Structure

### Primary Log File: app.log

**Format:**
```
YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE
```

**Content Categories:**
1. **System Events**: Server lifecycle, configuration changes
2. **Request Logs**: HTTP traffic, client interactions
3. **Processing Logs**: Query handling, model operations
4. **API Logs**: External service communications
5. **Error Logs**: Exceptions, failures, debugging information

### Log Levels Used

- **INFO**: Normal operations, request processing, API calls
- **WARNING**: Non-critical issues, deprecation notices
- **ERROR**: Exceptions, API failures, processing errors

## Security and Privacy Considerations

### Data Redaction
- API keys are marked as "REDACTED" in logs
- User queries are truncated to protect privacy
- Sensitive configuration data is masked

### Information Exposure
The logs contain:
- **Safe Information**: Timestamps, status codes, processing metrics
- **Potentially Sensitive**: System prompts, partial user queries, model responses
- **Protected Information**: API keys, full user content (redacted)

## Quality Assurance Information

### Model Performance Tracking
- Response generation times
- API success/failure rates
- Model parameter effectiveness
- Error pattern analysis

### System Health Monitoring
- Request processing latency
- API endpoint availability
- Search operation performance
- Error frequency and types

### Debugging Capabilities
- Complete request/response cycles
- Parameter validation results
- Model behavior analysis
- Integration point monitoring

## Usage for Quality Improvement

### 1. Performance Optimization
- Identify slow API calls
- Monitor response times
- Track resource utilization
- Optimize model parameters

### 2. Error Analysis
- Categorize failure types
- Identify problematic queries
- Monitor API reliability
- Debug integration issues

### 3. User Experience Enhancement
- Analyze query patterns
- Monitor response quality
- Track feature usage
- Identify improvement opportunities

### 4. System Reliability
- Monitor uptime and availability
- Track error rates
- Identify bottlenecks
- Ensure consistent performance

## Conclusion

The RAG Interface logging system provides comprehensive visibility into all aspects of the application's operation. From user interactions to API communications, every significant event is captured with sufficient detail to support debugging, performance optimization, and quality assurance efforts. The structured approach to logging ensures that developers and operators have the information needed to maintain and improve the system effectively.
