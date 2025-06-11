# Detailed Differences: main.py vs. app.py

## 1. Imports & Dependencies

**Shared imports**  
- Flask core:  
  - [`from flask import Flask, ...`](main.py:5)  
  - [`from flask import Flask, ...`](app.py:1)

**Unique to main.py**  
- Summary helper:  
  - [`from llm_summary_compact import summarize_batch_comparison`](main.py:13)  
- Traceback:  
  - [`import traceback`](main.py:9)

**Unique to app.py**  
- CORS support:  
  - [`from flask_cors import CORS`](app.py:2)  
- Time utilities:  
  - [`import time`](app.py:7)  
  - [`from datetime import datetime`](app.py:8)  
- Evaluation components:  
  - [`from evaluator import PromptEvaluator`](app.py:17)  
  - [`from evaluation_parser import parse_evaluation`](app.py:18)  
- Configuration module:  
  - [`from config import *`](app.py:20)

---

## 2. Logging Configuration

**main.py**  
- Uses `logging.basicConfig` once:  
  ```python
  logging.basicConfig(
      level=logging.WARNING,
      format='%(asctime)s - %(levelname)s - %(message)s',
      handlers=[
          logging.FileHandler("app.log"),
          logging.StreamHandler()
      ]
  )
  ```  
  ([main.py:21–28])

**app.py**  
- Creates module logger manually:  
  ```python
  logger = logging.getLogger(__name__)
  logger.handlers.clear()
  logger.addHandler(FileHandler('app.log'))
  logger.addHandler(StreamHandler(sys.stdout))
  logger.setLevel(logging.DEBUG)
  ```  
  ([app.py:23–35])

---

## 3. Assistant Initialization

**main.py**  
- Instantiates `FlaskRAGAssistant` **per request**, passing dynamic `settings`:  
  ```python
  assistant = FlaskRAGAssistant(settings=settings)
  ```  
  (e.g. [main.py:62], [main.py:101], [main.py:140])

**app.py**  
- Instantiates once **at startup**, storing in global `rag_assistant`:  
  ```python
  rag_assistant = FlaskRAGAssistant()
  ```  
  ([app.py:43–49])

---

## 4. Routes & Endpoints

| Endpoint         | main.py handlers                                 | app.py handlers                                         |
|------------------|--------------------------------------------------|----------------------------------------------------------|
| `/`              | [`index()`](main.py:31) → renders `index.html`   | [`index()`](app.py:53) → renders `index.html`            |
| `/api/query`     | POST → general RAG query ([main.py:84–107])      | POST → `query()` with CORS ([app.py:63–154])             |
| `/api/eval`      | POST → developer eval ([main.py:35–83])          | _Not present_                                            |
| `/api/system_prompt` | _Not present_                                | GET → returns default prompt ([app.py:58–62])            |
| `/api/reask`     | POST → multiple runs ([main.py:113–203])         | _Not present_                                            |
| `/api/smash`     | POST → compare two batches ([main.py:209–349])   | _Not present_                                            |
| `/api/save_config` | POST → save JSON config ([main.py:355–373])    | _Not present_                                            |
| `/api/load_configs` | GET → list saved configs ([main.py:378–406])   | _Not present_                                            |
| `/api/evaluate`  | _Not present_                                    | POST → evaluation pipeline ([app.py:163–268])           |
| `/api/export`    | _Not present_                                    | POST → export session markdown ([app.py:278–406])       |
| `/api/health`    | _Not present_                                    | GET → health check ([app.py:409–416])                   |

---

## 5. Error Handling & Utilities

- **404 Handlers**  
  - **main.py**:  
    ```python
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        return render_template('index.html')
    ```  
    ([main.py:408–412])

  - **app.py**:  
    ```python
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    ```  
    ([app.py:418–419])

- **500 Handlers**  
  - Only in **app.py**:  
    ```python
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    ```  
    ([app.py:422–424])

- **CORS**  
  - **app.py** enables CORS globally:  
    ```python
    CORS(app)
    ```  
    ([app.py:40])

- **Summary Flag**  
  - **main.py** defines `HAS_SUMMARY` to conditionally use batch summary:  
    ```python
    try:
        from llm_summary_compact import summarize_batch_comparison
        HAS_SUMMARY = True
    except ImportError:
        HAS_SUMMARY = False
    ```  
    ([main.py:12–16])

---

## 6. Conclusions

- **main.py** is focused on developer‐centric evaluation modes (`/api/eval`, `/api/reask`, `/api/smash`) with per‐request assistant instantiation and optional summary generation.  
- **app.py** is serving a user interface with persistent `rag_assistant`, CORS support, session export, evaluation pipeline, and health checks.  
- Logging and error handling are more robust in **app.py** (DEBUG level, JSON error handlers, CORS).

Use this report to guide refactoring or decide which functionalities to merge or decouple between the two Flask applications.