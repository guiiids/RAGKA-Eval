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
    return render_template('index.html')

@app.route('/api/system_prompt', methods=['GET'])
def system_prompt():
    """Return the default system prompt"""
    return jsonify({'system_prompt': rag_assistant.system_prompt if rag_assistant else ''})

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400

        query_text = data['query']
        model = data.get('model', 'gpt-4o')
        system_prompt = data.get('system_prompt', rag_assistant.system_prompt)
        appended_prompt = data.get('appended_prompt', '')
        temperature = data.get('temperature', 0.7)
        top_k = data.get('top_k', 50)
        top_p = data.get('top_p', 0.9)
        max_tokens = data.get('max_tokens', 1000)

        logger.info(f"Processing query: {query_text[:100]}...")

        # --- RAG Step ---
        result = rag_assistant.query(
            query=query_text,
            deployment=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            appended_prompt=appended_prompt
        )
        answer, sources = result[0], result[1]

        # Format full sources/context for display and for evaluator
        formatted_sources = []
        full_context = ""
        if sources:
            for i, source in enumerate(sources, 1):
                content = source.get('content', '') if isinstance(source, dict) else str(source)
                title = source.get('title', f'Source {i}') if isinstance(source, dict) else f'Source {i}'
                score = source.get('score', 0) if isinstance(source, dict) else 0
                formatted_sources.append({'title': title, 'content': content, 'score': score})
                full_context += f"\n### Source {i}: {title}\n{content}\n"

        # --- Casefile for Evaluator LLM ---
        casefile = f"""
## Session Information
- Timestamp: {datetime.now().isoformat()}
- Model: {model}
- Parameters: temperature={temperature}, top_k={top_k}, top_p={top_p}, max_tokens={max_tokens}

## Query
{query_text}

## System Prompt
{system_prompt}

## Appended Prompt
{appended_prompt}

## Model Parameters
temperature={temperature}, top_k={top_k}, top_p={top_p}, max_tokens={max_tokens}

## Response
{answer}

## Sources
{full_context}
"""

        # --- Evaluation Step ---
        from evaluation_model import EvaluationModel
        eval_model = EvaluationModel(model=model)
        diagnostic = eval_model.evaluate_case_file(casefile)

        response_data = {
            'answer': answer,
            'sources': formatted_sources,
            'model': model,
            'temperature': temperature,
            'top_k': top_k,
            'top_p': top_p,
            'max_tokens': max_tokens,
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'evaluation': diagnostic
        }
        logger.info("Query+Evaluation complete")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in /api/query: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """Handle evaluation requests using EvaluationModel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Validate required evaluation fields
        required_fields = ['user_query', 'system_prompt', 'model_response', 'sources']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({'error': 'Missing fields', 'missing_fields': missing}), 400

        from evaluation_model import EvaluationModel
        eval_model = EvaluationModel(model=data.get('model'))
        diagnostic = eval_model.evaluate(
            data['user_query'],
            data['system_prompt'],
            data['model_response'],
            data['sources']
        )
        return jsonify({'diagnostic': diagnostic}), 200

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
