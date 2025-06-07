import re
from pathlib import Path
from openai import AzureOpenAI
from config import OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, OPENAI_API_VERSION

class PromptEvaluator:
    """
    PromptEvaluator uses the enhanced system prompt from memory-bank/sys_prompt_enhanced.md
    to evaluate RAG chatbot system prompts. It performs a diagnostic evaluation based on:
      - User_Query
      - Retrieved_Context
      - Bot_Response
      - Bot_Instructions
    """

    def __init__(self, deployment: str = None):
        self.system_prompt = self._load_prompt()
        endpoint = OPENAI_ENDPOINT
        key = AZURE_OPENAI_API_KEY
        version = OPENAI_API_VERSION or "2023-05-15"
        # Initialize AzureOpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=version
        )
        # Use provided deployment or default to gpt-4
        self.deployment = deployment or "gpt-4"

    def _load_prompt(self) -> str:
        """
        Reads memory-bank/sys_prompt_enhanced.md and extracts the triple-quoted prompt string.
        """
        raw = Path("memory-bank/sys_prompt_enhanced.md").read_text(encoding="utf-8")
        match = re.search(r'CHAT_SYSTEM_PROMPT_ENHANCED\\s*=\\s*"""(.*)"""', raw, re.S)
        if match:
            return match.group(1).strip()
        # Fallback: return full file if extraction fails
        return raw

    def evaluate(
        self,
        user_query: str,
        retrieved_context: str,
        bot_response: str,
        bot_instructions: str
    ) -> str:
        """
        Performs a diagnostic evaluation and returns the evaluation report in Markdown.
        """
        user_content = (
            f"- User_Query: {user_query}\n"
            f"- Retrieved_Context: {retrieved_context}\n"
            f"- Bot_Response: {bot_response}\n"
            f"- Bot_Instructions: {bot_instructions}"
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]

        # Call the Azure OpenAI chat completion endpoint
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.0,
            max_completion_tokens=1000
        )
        return response.choices[0].message.content
