# Evaluation Model Implementation Plan

## Overview
Plan to implement a standalone Evaluation LLM model for `/api/evaluate` that parses full Markdown interactions, detects structural errors, and generates a diagnostic report per specification—without modifying the existing `FactChecker`.

## Steps
1. Inspect existing infrastructure  
   * Read `evaluator.py` to understand the current `FactChecker` usage  
   * Review `config.py` for model settings and deployments  
   * Locate any existing prompt templates in `rag_assistant.py` or `modeling.py`  

2. Design `EvaluationModel` class  
   * Create `models/evaluation_model.py`  
   * Responsibilities:  
     - Parse a full Markdown interaction into sections (`Session Information`, `Query`, `System Prompt`, `Appended Prompt`, `Model Parameters`, `Response`, `Sources`)  
     - Detect structural errors in headings and validate order  
     - Assemble a system prompt per the “Prompt Diagnostician’s Mandate” spec  
     - Call the LLM with formatted messages and return a structured report  

3. Integrate into Flask endpoint  
   * In `app.py:evaluate()`, add logic to:  
     1. Accept a single JSON field `document` (full Markdown) or file upload  
     2. Pass `document` to `EvaluationModel.evaluate(document)`  
     3. Receive the diagnostic report as a `dict`  
     4. **Then** retain existing `FactChecker` evaluation on `query`/`answer`/`context` if desired (no changes to `FactChecker`)  
     5. Merge both outputs (diagnostic report + fact-check scores) into the final JSON response  

4. Prompt engineering  
   * Create `prompts/evaluation_template.txt` containing the full specification text  
   * Load and format the template around the user-provided `document`  

5. Testing  
   * Add unit tests in `test_evaluation_model.py`  
   * Test cases include:  
     - Well-formed document returns correctly structured report  
     - Missing or misordered headings triggers a structural-error flag  
     - Interaction with `FactChecker` remains unaffected  

6. Documentation  
   * Update `README.md` with new endpoint usage examples  
   * Add module description and examples in `docs`  

## Flow Diagram
```mermaid
flowchart LR
  A[POST /api/evaluate] --> B[Flask evaluate()]
  B --> C[If document provided → EvaluationModel.evaluate(document)]
  C --> D[Parse Markdown & Detect Errors]
  D --> E[Call LLM → Diagnostic Report]
  E --> F[Return report]
  B --> G[Existing FactChecker.evaluate_response]
  G --> H[Fact-check scores]
  F --> I[Merge report + scores → jsonify response]