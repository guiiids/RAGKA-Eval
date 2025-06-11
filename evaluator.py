import logging
import re
from openai import AzureOpenAI
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

logger = logging.getLogger(__name__)


class PromptEvaluator:
    """
    Analyzes provided User_Query, Retrieved_Context, Bot_Response, and Bot_Instructions,
    flags missing or malformed sections, and returns a structured evaluation report
    in the prescribed schema.
    """

    REQUIRED_SECTIONS = [
        "User_Query",
        "Retrieved_Context",
        "Bot_Response",
        "Bot_Instructions",
    ]

    def __init__(self, model: str = None):
        endpoint = OPENAI_ENDPOINT
        api_key = AZURE_OPENAI_API_KEY or OPENAI_KEY
        api_version = OPENAI_API_VERSION
        deployment = model or MODEL_DEPLOYMENTS.get("gpt-4o")
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
        logger.info("PromptEvaluator initialized with deployment: %s", deployment)

    def evaluate(
        self,
        user_query: str,
        retrieved_context: str,
        bot_response: str,
        bot_instructions: str,
    ) -> str:
        """
        Perform evaluation. Check for missing or empty sections and then
        invoke the LLM to generate a Markdown evaluation report.
        """
        missing = []
        fields = {
            "User_Query": user_query,
            "Retrieved_Context": retrieved_context,
            "Bot_Response": bot_response,
            "Bot_Instructions": bot_instructions,
        }
        for name, content in fields.items():
            if not content or not content.strip():
                missing.append(name)

        if missing:
            error_lines = ["## Input Errors"]
            for sec in missing:
                error_lines.append(f"- Missing or empty section: {sec}")
            return "\n".join(error_lines)

        # Build system prompt with the required schema
        schema = """\
## Evaluation Metrics

- **Overall Score**: <score>
- **Relevance**: <relevance>
- **Accuracy**: <accuracy>
- **Completeness**: <completeness>
- **Clarity**: <clarity>
- **Question Understood**: <yes/partial/no>
- **Response Type**: <type>
- **Effectiveness**: <yes/partial/no>
- **Factually Correct**: <yes/partial/no>
- **Engagement**: <level>
- **Confidence**: <score>
- **Context Usage**: <assessment>

## Detailed Analysis

<analysis>

## Suggestions

<recommendation 1>

<recommendation 2>

...

## Full Evaluation

Evaluation Report
1. Overall Assessment
<text>

2. Detailed Analysis
<text>

3. Actionable Recommendations
<text>
"""
        system_prompt = (
            "You are a Prompt Diagnostician. Analyze the provided User_Query, Retrieved_Context, "
            "Bot_Response, and Bot_Instructions. If any sections are missing, flag them. Otherwise, "
            "produce a report strictly following this schema:\n\n"
            + schema
        )

        # Assemble user content
        user_content = (
            "### User_Query\n"
            + user_query.strip()
            + "\n\n### Retrieved_Context\n"
            + retrieved_context.strip()
            + "\n\n### Bot_Response\n"
            + bot_response.strip()
            + "\n\n### Bot_Instructions\n"
            + bot_instructions.strip()
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        logger.info("PromptEvaluator: invoking LLM with deployment: %s", self.deployment)
        resp = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_completion_tokens=1500,
            temperature=0.0,
        )
        content = resp.choices[0].message.content
        return content.strip()