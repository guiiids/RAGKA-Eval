import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
import json
import logging
from rag_assistant import FlaskRAGAssistant
import traceback

# Try to import the summary modules if present
try:
    from llm_summary_compact import summarize_batch_comparison
    HAS_SUMMARY = True
except ImportError:
    HAS_SUMMARY = False

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/eval', methods=['POST'])
def eval_mode():
    """Developer evaluation mode - single query with parameters"""
    try:
        logger.info(f"Received query request with data: {request.json!r}")
        data = request.json
        logger.info(f"Received eval request with data: {data}")
        
        query = data.get('query', '')
        system_prompt = data.get('system_prompt', '')
        temperature = float(data.get('temperature', 0.3))
        top_p = float(data.get('top_p', 1.0))
        max_tokens = int(data.get('max_tokens', 1000))
        
        logger.info(f"Eval mode: Query: {query!r}")
        logger.info(f"Eval mode: Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")
        
        settings = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        
        if system_prompt:
            settings["system_prompt"] = system_prompt
            settings["system_prompt_mode"] = "Override"
            
        assistant = FlaskRAGAssistant(settings=settings)
        actual_prompt = getattr(assistant, "DEFAULT_SYSTEM_PROMPT", "")
        logger.info(f"Eval mode: System prompt sent to AzureOpenAI: {actual_prompt!r}")
        
        answer, sources, _, evaluation, context = assistant.generate_rag_response(query)
        
        # Log the response details for debugging
        logger.info(f"Eval mode: Answer received: {answer[:100]}...")
        logger.info(f"Eval mode: Sources count: {len(sources) if sources else 0}")
        
        result = {
            "answer": answer,
            "sources": sources,
            "evaluation": evaluation
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Eval mode error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_mode():
    """General query endpoint wrapping RAG response generation"""
    try:
        logger.info(f"Received query request with data: {request.json!r}")
        data = request.json
        query = data.get('query', '')
        model = data.get('model', '')
        temperature = float(data.get('temperature', 0.3))
        top_p = float(data.get('top_p', 1.0))
        max_tokens = int(data.get('max_tokens', 1000))
        logger.info(f"Query mode: Query={query!r}, Model={model}, Temp={temperature}, Top-P={top_p}, MaxTokens={max_tokens}")
        settings = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        if model:
            settings["model"] = model
        assistant = FlaskRAGAssistant(settings=settings)
        answer, sources, _, evaluation, context = assistant.generate_rag_response(query)
        logger.info(f"Query mode: Answer received: {answer[:100]}...")
        logger.info(f"Query mode: Sources count: {len(sources)}")
        return jsonify({"answer": answer, "sources": sources, "evaluation": evaluation})
    except Exception as e:
        logger.error(f"Query mode error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/reask', methods=['POST'])
def reask_mode():
    """ReAsk mode - same query multiple times with same parameters"""
    try:
        data = request.json
        logger.info(f"Received reask request with data: {data}")
        
        query = data.get('query', '')
        system_prompt = data.get('system_prompt', '')
        temperature = float(data.get('temperature', 0.3))
        top_p = float(data.get('top_p', 1.0))
        max_tokens = int(data.get('max_tokens', 1000))
        n_runs = int(data.get('n_runs', 1))
        
        logger.info(f"ReAsk mode: Query: {query!r}, Runs: {n_runs}")
        logger.info(f"ReAsk mode: Parameters: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")
        
        settings = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
            
        if system_prompt:
            settings["system_prompt"] = system_prompt
            settings["system_prompt_mode"] = "Override"
        
        assistant = FlaskRAGAssistant(settings=settings)
        actual_prompt = getattr(assistant, "DEFAULT_SYSTEM_PROMPT", "")
        logger.info(f"ReAsk mode: System prompt sent to AzureOpenAI: {actual_prompt!r}")
        
        results = []
        for i in range(n_runs):
            try:
                logger.info(f"ReAsk mode Run {i+1}: Query: {query!r}")
                answer, sources, _, evaluation, context = assistant.generate_rag_response(query)
                logger.info(f"ReAsk mode Run {i+1}: Answer: {answer[:100]}...")
                logger.info(f"ReAsk mode Run {i+1}: Sources count: {len(sources) if sources else 0}")
                
                results.append({
                    "run": i+1,
                    "answer": answer,
                    "sources": sources,
                    "evaluation": evaluation,
                    "context": context
                })
            except Exception as e:
                logger.error(f"ReAsk mode Error on run {i+1}: {e}")
                logger.error(traceback.format_exc())
                results.append({
                    "run": i+1,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Generate summary if available
        summary = None
        if HAS_SUMMARY:
            try:
                summary_data = {
                    "query": query,
                    "parameters": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "max_tokens": max_tokens,
                        "system_prompt": system_prompt
                    },
                    "results": results
                }
                summary = summarize_batch_comparison(summary_data)
                logger.info(f"ReAsk mode: Generated summary: {summary[:100]}...")
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                summary = f"Error generating summary: {e}"
        
        response_data = {
            "query": query,
            "parameters": {
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "system_prompt": system_prompt
            },
            "results": results,
            "summary": summary
        }
        
        # Log the full response structure (without full content)
        logger.info(f"ReAsk mode: Returning response with {len(results)} results and summary: {bool(summary)}")
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"ReAsk mode error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/smash', methods=['POST'])
def smash_mode():
    """Smash mode - compare two different parameter sets"""
    try:
        data = request.json
        logger.info(f"Received smash request with data: {data}")
        
        query = data.get('query', '')
        
        # Batch 1 params
        system_prompt1 = data.get('system_prompt1', '')
        temp1 = float(data.get('temperature1', 0.3))
        top_p1 = float(data.get('top_p1', 1.0))
        max_tokens1 = int(data.get('max_tokens1', 1000))
        n_runs1 = int(data.get('n_runs1', 1))
        
        # Batch 2 params
        system_prompt2 = data.get('system_prompt2', '')
        temp2 = float(data.get('temperature2', 0.3))
        top_p2 = float(data.get('top_p2', 1.0))
        max_tokens2 = int(data.get('max_tokens2', 1000))
        n_runs2 = int(data.get('n_runs2', 1))
        
        logger.info(f"Smash mode: Query: {query!r}")
        logger.info(f"Smash mode: Batch 1 params: prompt={system_prompt1!r}, temp={temp1}, top_p={top_p1}, max_tokens={max_tokens1}, n_runs={n_runs1}")
        logger.info(f"Smash mode: Batch 2 params: prompt={system_prompt2!r}, temp={temp2}, top_p={top_p2}, max_tokens={max_tokens2}, n_runs={n_runs2}")
        
        # Run batch 1
        batch1_params = {
            "temperature": temp1,
            "top_p": top_p1,
            "max_tokens": max_tokens1
        }
        if system_prompt1:
            batch1_params["system_prompt"] = system_prompt1
            batch1_params["system_prompt_mode"] = "Override"
            
        assistant1 = FlaskRAGAssistant(settings=batch1_params)
        actual_prompt1 = getattr(assistant1, "DEFAULT_SYSTEM_PROMPT", "")
        logger.info(f"Smash mode: Batch 1 System prompt: {actual_prompt1!r}")
        
        batch1_results = []
        for i in range(n_runs1):
            try:
                logger.info(f"Smash mode Batch 1 Run {i+1}: Query: {query!r}")
                answer, sources, _, evaluation, context = assistant1.generate_rag_response(query)
                logger.info(f"Smash mode Batch 1 Run {i+1}: Answer: {answer[:100]}...")
                logger.info(f"Smash mode Batch 1 Run {i+1}: Sources count: {len(sources) if sources else 0}")
                
                batch1_results.append({
                    "run": i+1,
                    "answer": answer,
                    "sources": sources,
                    "evaluation": evaluation,
                    "context": context
                })
            except Exception as e:
                logger.error(f"Smash mode Batch 1 Error on run {i+1}: {e}")
                logger.error(traceback.format_exc())
                batch1_results.append({
                    "run": i+1,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Run batch 2
        batch2_params = {
            "temperature": temp2,
            "top_p": top_p2,
            "max_tokens": max_tokens2
        }
        if system_prompt2:
            batch2_params["system_prompt"] = system_prompt2
            batch2_params["system_prompt_mode"] = "Override"
            
        assistant2 = FlaskRAGAssistant(settings=batch2_params)
        actual_prompt2 = getattr(assistant2, "DEFAULT_SYSTEM_PROMPT", "")
        logger.info(f"Smash mode: Batch 2 System prompt: {actual_prompt2!r}")
        
        batch2_results = []
        for i in range(n_runs2):
            try:
                logger.info(f"Smash mode Batch 2 Run {i+1}: Query: {query!r}")
                answer, sources, _, evaluation, context = assistant2.generate_rag_response(query)
                logger.info(f"Smash mode Batch 2 Run {i+1}: Answer: {answer[:100]}...")
                logger.info(f"Smash mode Batch 2 Run {i+1}: Sources count: {len(sources) if sources else 0}")
                
                batch2_results.append({
                    "run": i+1,
                    "answer": answer,
                    "sources": sources,
                    "evaluation": evaluation,
                    "context": context
                })
            except Exception as e:
                logger.error(f"Smash mode Batch 2 Error on run {i+1}: {e}")
                logger.error(traceback.format_exc())
                batch2_results.append({
                    "run": i+1,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        
        # Generate comparison summary if available
        comparison_summary = None
        if HAS_SUMMARY:
            try:
                comparison_data = {
                    "query": query,
                    "batch_1": {
                        "parameters": batch1_params,
                        "results": batch1_results
                    },
                    "batch_2": {
                        "parameters": batch2_params,
                        "results": batch2_results
                    }
                }
                comparison_summary = summarize_batch_comparison(comparison_data)
                logger.info(f"Smash mode: Generated comparison summary: {comparison_summary[:100]}...")
            except Exception as e:
                logger.error(f"Error generating comparison summary: {e}")
                comparison_summary = f"Error generating comparison summary: {e}"
        
        response_data = {
            "query": query,
            "batch_1": {
                "parameters": batch1_params,
                "results": batch1_results
            },
            "batch_2": {
                "parameters": batch2_params,
                "results": batch2_results
            },
            "comparison_summary": comparison_summary
        }
        
        # Log the full response structure (without full content)
        logger.info(f"Smash mode: Returning response with batch1: {len(batch1_results)} results, batch2: {len(batch2_results)} results, and summary: {bool(comparison_summary)}")
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Smash mode error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_config', methods=['POST'])
def save_config():
    """Save a configuration for later use"""
    try:
        data = request.json
        logger.info(f"Saving configuration: {data.get('name')}")
        
        config_name = data.get('name', 'Unnamed Config')
        config_data = data.get('config', {})
        
        # Create configs directory if it doesn't exist
        os.makedirs('configs', exist_ok=True)
        
        # Save config to file
        filename = f"configs/{config_name.replace(' ', '_').lower()}.json"
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        return jsonify({"success": True, "message": f"Configuration saved as {config_name}"})
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/load_configs', methods=['GET'])
def load_configs():
    """Load all saved configurations"""
    try:
        configs = []
        
        # Create configs directory if it doesn't exist
        os.makedirs('configs', exist_ok=True)
        
        # List all config files
        config_files = [f for f in os.listdir('configs') if f.endswith('.json')]
        
        for filename in config_files:
            try:
                with open(f"configs/{filename}", 'r') as f:
                    config_data = json.load(f)
                    config_name = filename.replace('.json', '').replace('_', ' ').title()
                    configs.append({
                        "name": config_name,
                        "config": config_data
                    })
            except Exception as e:
                logger.error(f"Error loading config {filename}: {e}")
        
        return jsonify({"configs": configs})
    except Exception as e:
        logger.error(f"Error loading configurations: {e}")
        return jsonify({"error": str(e)}), 500

# Catch-all 404 error handler for API endpoints
@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return render_template('index.html')
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
