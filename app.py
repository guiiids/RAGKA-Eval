from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import logging
import sys
import os
import time
from datetime import datetime

# Import the RAG assistant
try:
    from rag_assistant import FlaskRAGAssistant
except ImportError:
    FlaskRAGAssistant = None

from config import *

# Configure logging
logger = logging.getLogger(__name__)
if logger.handlers:
    logger.handlers.clear()

file_handler = logging.FileHandler('app.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

logger.info("RAG Assistant Interface starting up")

app = Flask(__name__)

# Initialize RAG assistant
try:
    if FlaskRAGAssistant:
        rag_assistant = FlaskRAGAssistant()
        logger.info("RAG Assistant initialized successfully")
    else:
        rag_assistant = None
        logger.warning("FlaskRAGAssistant not available")
except Exception as e:
    logger.error(f"Failed to initialize RAG Assistant: {e}")

@app.route('/')
def index():
    """Serve the main interface"""
    return send_from_directory('.', 'index.html')

@app.route('/api/system_prompt', methods=['GET'])
def system_prompt():
    """Return the default system prompt"""
    return jsonify({'system_prompt': rag_assistant.system_prompt if rag_assistant else ''})

@app.route('/api/query', methods=['POST'])
def query():
    """Handle query requests from the interface"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query_text = data['query']
        model = data.get('model', 'gpt-4o')
        appended_prompt = data.get('appended_prompt', '')
        temperature = data.get('temperature', 0.7)
        top_k = data.get('top_k', 50)
        top_p = data.get('top_p', 0.9)
        max_tokens = data.get('max_tokens', 1000)
        
        logger.info(f"Processing query: {query_text[:100]}...")
        logger.info(f"Parameters - Model: {model}, Temp: {temperature}, Top-K: {top_k}, Top-P: {top_p}")
        
        start_time = time.time()
        
        
        # Real mode - use RAG assistant
        if not rag_assistant:
            return jsonify({'error': 'RAG Assistant not available. Please check your Azure configuration.'}), 500
        
        # Call the RAG assistant
        result = rag_assistant.query(
            query=query_text,
            deployment=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            appended_prompt=appended_prompt
        )
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # Convert to milliseconds
        
        # Extract answer and sources from result
        if isinstance(result, tuple) and len(result) >= 2:
            answer, sources = result[0], result[1]
        else:
            answer = str(result)
            sources = []
        
        # Format sources for display
        formatted_sources = []
        if sources:
            for i, source in enumerate(sources[:5]):  # Limit to 5 sources
                if isinstance(source, dict):
                    formatted_sources.append({
                        'title': source.get('title', f'Source {i+1}'),
                        'content': source.get('content', '')[:200] + '...' if len(source.get('content', '')) > 200 else source.get('content', ''),
                        'score': source.get('score', 0)
                    })
                else:
                    formatted_sources.append({
                        'title': f'Source {i+1}',
                        'content': str(source)[:200] + '...' if len(str(source)) > 200 else str(source),
                        'score': 0
                    })
        
        response_data = {
            'answer': answer,
            'sources': formatted_sources,
            'model': model,
            'temperature': temperature,
            'top_k': top_k,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'response_time': response_time,
            'token_count': len(answer.split()) if answer else 0,  # Rough token estimate
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Query processed successfully in {response_time}ms")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """Handle evaluation requests"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data or 'answer' not in data:
            return jsonify({'error': 'Query and answer are required'}), 400
        
        query_text = data['query']
        answer = data['answer']
        sources = data.get('sources', [])
        
        logger.info(f"Evaluating response for query: {query_text[:100]}...")
        
        # Actual evaluation using FactChecker
        context = data.get('context', '')
        model = data.get('model', rag_assistant.deployment_name)
        evaluation = rag_assistant.fact_checker.evaluate_response(
            query=query_text,
            answer=answer,
            context=context,
            deployment=model
        )
        logger.info("Evaluation completed successfully")
        return jsonify(evaluation)
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'rag_assistant': 'available' if rag_assistant else 'unavailable',
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Use a different port (5005) to avoid conflicts
    port = 5005
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port} with debug={debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
