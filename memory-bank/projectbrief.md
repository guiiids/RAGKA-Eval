# Project Brief: RAG Assistant Interface

## Project Overview
The RAG Assistant Interface is a web application that provides a modern interface for interacting with a Retrieval-Augmented Generation (RAG) assistant powered by Azure OpenAI. The application allows users to query a knowledge base using natural language, with responses generated by Azure OpenAI models enhanced by relevant context retrieved from Azure Cognitive Search.

## Core Requirements
1. Provide a user-friendly web interface for interacting with the RAG assistant
2. Connect to Azure OpenAI for generating responses
3. Integrate with Azure Cognitive Search for knowledge retrieval
4. Support configuration of model parameters
5. Evaluate response quality in real-time
6. Display sources used in generating responses

## Technical Goals
1. Create a responsive web interface that works on desktop and mobile
2. Implement secure configuration management using environment variables
3. Develop a robust backend API for processing queries
4. Ensure proper error handling and logging
5. Provide clear documentation for setup and usage

## Current Status
The application is experiencing an error with the Azure OpenAI API deployment. The error message indicates that the deployment specified in the configuration doesn't exist or isn't properly set up:
```
openai.NotFoundError: Error code: 404 - {'error': {'code': 'DeploymentNotFound', 'message': 'The API deployment for this resource does not exist. If you created the deployment within the last 5 minutes, please wait a moment and try again.'}}
```

## Next Steps
1. Diagnose and fix the OpenAI API deployment error
2. Ensure proper configuration of Azure OpenAI and Azure Cognitive Search
3. Test the application with various queries
4. Improve error handling and user feedback
