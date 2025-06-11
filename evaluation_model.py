import logging
from openai import AzureOpenAI

logger = logging.getLogger(__name__)
from config import (
    MODEL_DEPLOYMENTS,
    MODEL_ENDPOINTS,
    MODEL_KEYS,
    MODEL_API_VERSIONS,
    AZURE_OPENAI_API_KEY,
    OPENAI_ENDPOINT,
    OPENAI_KEY,
    OPENAI_API_VERSION,
)

class EvaluationModel:
    """
    Evaluates a user query, system prompt, model response, and sources
    using an LLM Prompt Diagnostician.
    """
    def __init__(self, model: str = None):
        # Configure Azure OpenAI client
        endpoint = OPENAI_ENDPOINT
        api_key = AZURE_OPENAI_API_KEY or OPENAI_KEY
        api_version = OPENAI_API_VERSION
        deployment = model or MODEL_DEPLOYMENTS.get("gpt-4o")
        # Allow overrides from MODEL_ENDPOINTS/MODEL_KEYS/MODEL_API_VERSIONS
        if deployment in MODEL_ENDPOINTS and MODEL_ENDPOINTS[deployment]:
            endpoint = MODEL_ENDPOINTS[deployment]
        if deployment in MODEL_KEYS and MODEL_KEYS[deployment]:
            api_key = MODEL_KEYS[deployment]
        if deployment in MODEL_API_VERSIONS and MODEL_API_VERSIONS[deployment]:
            api_version = MODEL_API_VERSIONS[deployment]
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version or "2023-05-15",
        )
        self.deployment = deployment
        logger.info("EvaluationModel initialized with deployment: %s", deployment)


    def evaluate(self, user_query: str, system_prompt: str, model_response: str, sources) -> dict:
    
        """
        Perform evaluation of four inputs: user_query, system_prompt, model_response, and sources.
        Returns a markdown-formatted diagnostic report or input errors.
        """
        missing_fields = []
        if not user_query or not user_query.strip():
            missing_fields.append("user_query")
        if not system_prompt or not system_prompt.strip():
            missing_fields.append("system_prompt")
        if not model_response or not model_response.strip():
            missing_fields.append("model_response")
        if not sources or (isinstance(sources, str) and not sources.strip()) or (isinstance(sources, list) and len(sources) == 0):
            missing_fields.append("sources")
        if missing_fields:
            return {
                "error": "Input Error",
                "missing_fields": missing_fields
            }

        # Format sources input into markdown text
        if isinstance(sources, list):
            formatted_sources = []
            for src in sources:
                if isinstance(src, dict):
                    title = src.get("title", "")
                    content = src.get("content", "")
                    formatted_sources.append(f"**{title}**: {content}")
                else:
                    formatted_sources.append(str(src))
            sources_str = "\n".join(formatted_sources)
        else:
            sources_str = sources

        # Assemble diagnostic prompt
        diagnostician_prompt = (
            "You are a Lead AI System Architect specializing in prompt engineering "
            "and RAG system diagnostics. Evaluate the effectiveness and robustness "
            "of the System Prompt based on the provided inputs. "
            "Return a markdown-formatted diagnostic report with sections: "
            "1. Overall Assessment, 2. Detailed Analysis, 3. Actionable Recommendations. "
            "Strictly follow the Prompt Diagnostician’s Mandate."
        )
        logger.info("EvaluationModel: using diagnostic prompt")
        user_content = (
            "### User Query\n"
            + user_query.strip()
            + "\n\n### System Prompt\n"
            + system_prompt.strip()
            + "\n\n### Model Response\n"
            + model_response.strip()
            + "\n\n### Sources\n"
            + sources_str.strip()
        )

        messages = [
            {"role": "system", "content": diagnostician_prompt},
            {"role": "user", "content": user_content}
        ]

        logger.info("EvaluationModel: invoking LLM with deployment: %s", self.deployment)
        resp = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_tokens=1000,
            temperature=0.0
        )
        content = resp.choices[0].message.content
        # Return raw markdown report
        return {"report": content.strip()}
    def evaluate_case_file(self, casefile_markdown: str) -> str:
        rubric_prompt = """
# Evaluation Rubric for RAG Chatbot System Prompt
The Prompt Diagnostician’s Mandate: Prompt for Evaluation LLM
-------------------------------------------------------------

You are a Lead AI System Architect specializing in prompt engineering and RAG system diagnostics. Your task is to evaluate the effectiveness and robustness of a RAG-based chatbot’s **System Prompt**—not merely a single end-user response—based on one representative interaction.You will receive these four inputs:

**Input File Structure: What You Will Receive**
-----------------------------------------------

You will always receive a single document  or text from input, representing a full exported RAG chatbot interaction, including all information needed for your analysis. The document is formatted in Markdown and contains the following sections, always in this order:

*   **Session Information:** Metadata including timestamp, model, and basic run parameters.
    
*   **Query:** The end-user’s question.
    
*   **System Prompt:** The exact instructions or “prompt” given to the chatbot.
    
*   **Appended Prompt:** Any supplemental prompt or rules added to the main prompt.
    
*   **Model Parameters:** The generation parameters (e.g., temperature, top\_k, top\_p).
    
*   **Response:** The bot’s generated answer to the user’s question.
    
*   **Sources:** The full text of all context data (“Retrieved\_Context”) that was presented to the chatbot for answering this query. Each source is typically labeled by file or document name and may be shown as a code block or quoted text. Multiple sources may appear, each separated and labeled.
    
*   **(Optional: Evaluation Metrics, Analysis, Suggestions, or other diagnostic sections—ignore these unless instructed otherwise.)**
    

**Section Boundaries and Formatting**
-------------------------------------

*   Each section starts with a clearly labeled Markdown heading (e.g., ## Query, ## System Prompt, ## Sources).
    
*   Source texts within the Sources section may appear as code blocks with a filename or identifier.
    
*   No section is omitted; if content is not present for a given section, the heading is still included.
    
*   **Key for the Reviewer LLM:**
    
    *   Parse and extract each section by its Markdown heading.
        
    *   Treat the “Sources” section as the _Retrieved\_Context_ for your evaluation framework.
        
    *   If any section is missing, malformed, or out of order, flag this as a structural error.
        
    *   You must return a markdown-formatted diagnostic report with the following required structure:
        
*   **1\. Overall Assessment**
    
    *   Summarize if the Bot\_Response _correctly_ answers the User\_Query, given the Retrieved\_Context and the Bot\_Instructions.
        
    *   Always state _immediately_ if the Retrieved\_Context was insufficient or off-topic for the User\_Query.
        
*   **2\. Detailed Analysis**
    
*   **Adherence to Instructions:**
    
    *   Did the Bot\_Response follow formatting, structure, and rules set by the System Prompt?
        
*   **Content Accuracy & Faithfulness:**
    
    *   Did the Bot\_Response use only the Retrieved\_Context?
        
    *   Did it avoid hallucination, invention, or supplementing with outside knowledge?
        
    *   If context is insufficient, explicitly say so (quote: “Retrieved\_Context does not contain information to fully answer the User\_Query.”).
        
*   **Clarity & Helpfulness:**
    
    *   Was the response organized, readable, and useful?
        
    *   Were steps/actions/logic presented in a way a user could follow?
        
    *   Any confusion or ambiguity present?
        
*   **3\. Actionable Recommendations**
    
*   List clear, concrete steps to improve the **System Prompt** itself so future responses avoid the same weaknesses.
    
    *   Each recommendation should be specific—e.g., “Add a rule requiring the bot to notify the user if the Retrieved\_Context is missing or inadequate.”
        
*   **Additional Notes for the LLM:**
    
    *   _Do not_ invent details—base your entire evaluation strictly on the retrieved context and supplied instructions.
        
    *   Use numbered lists for processes, bullet points for unordered recommendations.
        
    *   Match the markdown formatting shown in the gold standard example.
        
*   **Your task:**
    
    *   Analyze the provided User\_Query, Retrieved\_Context, Bot\_Response, and Bot\_Instructions.
        
    *   Return your evaluation _strictly_ in the structure above.
        
    *   If you encounter missing, malformed, or contradictory sections, flag these as input errors at the top of your output.
"""
        messages = [
            {"role": "system", "content": rubric_prompt.strip()},
            {"role": "user", "content": casefile_markdown.strip()}
        ]
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_tokens=1200,
            temperature=0.0,
        )
        return response.choices[0].message.content