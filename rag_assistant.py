"""
Flask-compatible version of the RAG assistant without Streamlit dependencies
"""
import logging
from typing import List, Dict, Tuple, Optional, Any, Generator, Union
import traceback
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
import re
import sys
import os
import json as _json
from evaluation_model import EvaluationModel

# Import config but handle the case where it might import streamlit
try:
    from config import (
        OPENAI_ENDPOINT,
        OPENAI_KEY,
        AZURE_OPENAI_API_KEY,
        OPENAI_API_VERSION,
        EMBEDDING_DEPLOYMENT,
        CHAT_DEPLOYMENT,
        SEARCH_ENDPOINT,
        SEARCH_INDEX,
        SEARCH_KEY,
        VECTOR_FIELD,
    )
except ImportError as e:
    if 'streamlit' in str(e):
        # Define fallback values or load from environment
        OPENAI_ENDPOINT = os.environ.get("OPENAI_ENDPOINT")
        OPENAI_KEY = os.environ.get("OPENAI_KEY")
        OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION")
        EMBEDDING_DEPLOYMENT = os.environ.get("EMBEDDING_DEPLOYMENT")
        CHAT_DEPLOYMENT = os.environ.get("CHAT_DEPLOYMENT")
        SEARCH_ENDPOINT = os.environ.get("SEARCH_ENDPOINT")
        SEARCH_INDEX = os.environ.get("SEARCH_INDEX")
        SEARCH_KEY = os.environ.get("SEARCH_KEY")
        VECTOR_FIELD = os.environ.get("VECTOR_FIELD")
    else:
        raise

logger = logging.getLogger(__name__)


class FlaskRAGAssistant:
    """Retrieval-Augmented Generation assistant for Azure OpenAI + Search."""

    # Default system prompt
    DEFAULT_SYSTEM_PROMPT = """
    ### Task:

    Respond to the user query using the provided context, incorporating inline citations in the format [id] **only when the <source> tag includes an explicit id attribute** (e.g., <source id="1">).
    
    ### Guidelines:

    - If you don't know the answer, clearly state that.
    - If uncertain, ask the user for clarification.
    - Respond in the same language as the user's query.
    - If the context is unreadable or of poor quality, inform the user and provide the best possible answer.
    - If the answer isn't present in the context but you possess the knowledge, explain this to the user and provide the answer using your own understanding.
    - **Only include inline citations using [id] (e.g., [1], [2]) when the <source> tag includes an id attribute.**
    - Do not cite if the <source> tag does not contain an id attribute.
    - Do not use XML tags in your response.
    - Ensure citations are concise and directly related to the information provided.
    
    ### Example of Citation:

    If the user asks about a specific topic and the information is found in a source with a provided id attribute, the response should include the citation like in the following example:

    * "According to the study, the proposed method increases efficiency by 20% [1]."
    
    ### Output:

    Provide a clear and direct response to the user's query, including inline citations in the format [id] only when the <source> tag with id attribute is present in the context.
    
    <context>

    {{CONTEXT}}
    </context>
    
    <user_query>

    {{QUERY}}
    </user_query>
    """

    # ───────────────────────── setup ─────────────────────────
    def __init__(self, settings=None) -> None:
        self._init_cfg()
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            api_key=self.openai_key,
            api_version=self.openai_api_version or "2023-05-15",
        )
        self.eval_model = EvaluationModel(model=self.deployment_name)
        
        # Model parameters with defaults
        self.temperature = 0.3
        self.top_p = 1.0
        self.max_tokens = 1000
        self.presence_penalty = 0.6
        self.frequency_penalty = 0.6
        
        # Load settings if provided
        self.settings = settings or {}
        self._load_settings()

    def _init_cfg(self) -> None:
        self.openai_endpoint      = OPENAI_ENDPOINT
        self.openai_key           = AZURE_OPENAI_API_KEY or OPENAI_KEY
        self.openai_api_version   = OPENAI_API_VERSION
        self.embedding_deployment = EMBEDDING_DEPLOYMENT
        self.deployment_name      = CHAT_DEPLOYMENT
        self.search_endpoint      = SEARCH_ENDPOINT
        self.search_index         = SEARCH_INDEX
        self.search_key           = SEARCH_KEY
        self.vector_field         = VECTOR_FIELD
        
    def _load_settings(self) -> None:
        """Load settings from provided settings dict"""
        settings = self.settings
        
        # Update model parameters
        if "model" in settings:
            self.deployment_name = settings["model"]
        if "temperature" in settings:
            self.temperature = settings["temperature"]
        if "top_p" in settings:
            self.top_p = settings["top_p"]
        if "max_tokens" in settings:
            self.max_tokens = settings["max_tokens"]
        
        # Update search configuration
        if "search_index" in settings:
            self.search_index = settings["search_index"]

    # ───────────── embeddings ─────────────
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        if not text:
            return None
        try:
            resp = self.openai_client.embeddings.create(
                model=self.embedding_deployment,
                input=text.strip(),
            )
            return resp.data[0].embedding
        except Exception as exc:
            logger.error("Embedding error: %s", exc)
            return None

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
        return 0.0 if mag == 0 else dot / mag

    # ───────────── Azure Search ───────────
    def search_knowledge_base(self, query: str) -> List[Dict]:
        try:
            client = SearchClient(
                endpoint=f"https://{self.search_endpoint}.search.windows.net",
                index_name=self.search_index,
                credential=AzureKeyCredential(self.search_key),
            )
            q_vec = self.generate_embedding(query)
            if not q_vec:
                return []

            vec_q = VectorizedQuery(
                vector=q_vec,
                k_nearest_neighbors=10,
                fields=self.vector_field,
            )
            results = client.search(
                search_text=query,
                vector_queries=[vec_q],
                select=["chunk", "title"],
                top=10,
            )
            return [
                {
                    "chunk": r.get("chunk", ""),
                    "title": r.get("title", "Untitled"),
                    "relevance": 1.0,
                }
                for r in results
            ]
        except Exception as exc:
            logger.error("Search error: %s", exc)
            return []
        
    # ───────── context & citations ────────
    def _prepare_context(self, results: List[Dict]) -> Tuple[str, Dict]:
        entries, src_map = [], {}
        sid = 1
        for res in results[:5]:
            chunk = res["chunk"].strip()
            if not chunk:
                continue
            entries.append(f'<source id="{sid}">{chunk}</source>')
            src_map[str(sid)] = {"title": res["title"], "content": chunk}
            sid += 1
        return "\n\n".join(entries), src_map

    def _chat_answer(self, query: str, context: str, src_map: Dict, appended_prompt: str = None) -> str:
        system_prompt = self.DEFAULT_SYSTEM_PROMPT
        
        settings = self.settings
        custom_prompt = settings.get("custom_prompt", "")
        system_override = settings.get("system_prompt", "")
        mode = settings.get("system_prompt_mode", "Append")

        if custom_prompt:
            query = f"{custom_prompt}\n\n{query}"
            logger.info("DEBUG - Applied custom prompt to query.")
        
        if system_override:
            if mode == "Override":
                system_prompt = system_override
            else:
                system_prompt = f"{system_override}\n\n{self.DEFAULT_SYSTEM_PROMPT}"

        if appended_prompt:
            system_prompt += f"\n{appended_prompt}"

        processed_system = system_prompt.strip()
        processed_user = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
        messages = [
            {"role": "system", "content": processed_system},
            {"role": "user", "content": processed_user}
        ]

        from config import MODEL_DEPLOYMENTS, MODEL_ENDPOINTS, MODEL_KEYS, MODEL_API_VERSIONS
        endpoint = self.openai_endpoint
        api_key = self.openai_key
        api_version = self.openai_api_version
        deployment_name = self.deployment_name
        if deployment_name in MODEL_ENDPOINTS and MODEL_ENDPOINTS[deployment_name]:
            endpoint = MODEL_ENDPOINTS[deployment_name]
        if deployment_name in MODEL_KEYS and MODEL_KEYS[deployment_name]:
            api_key = MODEL_KEYS[deployment_name]
        if deployment_name in MODEL_API_VERSIONS and MODEL_API_VERSIONS[deployment_name]:
            api_version = MODEL_API_VERSIONS[deployment_name]
        if deployment_name in MODEL_DEPLOYMENTS and MODEL_DEPLOYMENTS[deployment_name]:
            deployment_name = MODEL_DEPLOYMENTS[deployment_name]
        
        logger.info("========== OPENAI API REQUEST ==========")
        logger.info(f"deployment: {deployment_name}, temp: {self.temperature}, tokens: {self.max_tokens}, top_p: {self.top_p}, presence_penalty: {self.presence_penalty}, frequency_penalty: {self.frequency_penalty}")

        logger.info("========== SYSTEM PROMPT ==========")
        logger.info(processed_system)

        logger.info("========== USER CONTENT ==========")
        logger.info(processed_user)

        logger.info("========== MESSAGES ARRAY ==========")
        for i, message in enumerate(messages, 1):
            logger.info(f"Message {i} - Role: {message['role']}")
            logger.info(f"Content: {message['content']}")

        payload = {
            "model": deployment_name,
            "messages": messages,
            "max_completion_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty
        }
        logger.info("========== OPENAI RAW PAYLOAD ==========")
        logger.info(_json.dumps(payload, indent=2))

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version or "2023-05-15",
        )
        resp = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty
        )
        answer = resp.choices[0].message.content
        logger.info("DEBUG - OpenAI response content: %s", answer)
        logger.info("========== OPENAI API RESPONSE ==========")
        logger.info("Response content: %s", answer)
        if hasattr(resp, "usage"):
            logger.info("Token usage: prompt=%d, completion=%d", resp.usage.prompt_tokens, resp.usage.completion_tokens)
        return answer

    def _filter_cited(self, answer: str, src_map: Dict) -> List[Dict]:
        cited = []
        for sid, sinfo in src_map.items():
            if f"[{sid}]" in answer:
                entry = {"id": sid, "title": sinfo["title"], "content": sinfo["content"]}
                if "url" in sinfo:
                    entry["url"] = sinfo["url"]
                cited.append(entry)
        return cited

    # ─────────── public API ───────────────
    @property
    def system_prompt(self):
        return self.DEFAULT_SYSTEM_PROMPT

    def query(
        self, query: str, deployment: str = None, temperature: float = None, 
        top_p: float = None, max_tokens: int = None, appended_prompt: str = None
    ) -> Tuple[str, List[Dict]]:
        """
        Query method called by app.py - wrapper around generate_rag_response
        Returns just the answer and sources for simplicity
        """
        # Update settings if provided
        if deployment:
            self.deployment_name = deployment
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        if max_tokens is not None:
            self.max_tokens = max_tokens
            
        # Call the main response generation method
        answer, sources, _, _, _ = self.generate_rag_response(query, appended_prompt=appended_prompt)
        return answer, sources
        
    def generate_rag_response(
        self, query: str, appended_prompt: str = None
    ) -> Tuple[str, List[Dict], List[Dict], Dict[str, Any], str]:
        self._load_settings()
        kb_results = self.search_knowledge_base(query)
        if not kb_results:
            ans = self._chat_answer(query, "", {}, appended_prompt=appended_prompt)
            return ans, [], [], {}, ""
        context, src_map = self._prepare_context(kb_results)
        # Logging full context chunks before generating answer
        for src_id, src_data in src_map.items():
            logger.info(f"=== Source {src_id}: {src_data['title']} ===")
            logger.info(src_data['content'])
        ans = self._chat_answer(query, context, src_map, appended_prompt=appended_prompt)
        raw = self._filter_cited(ans, src_map)
        renum, cited = {}, []
        for i, src in enumerate(raw, 1):
            renum[src["id"]] = str(i)
            entry = {"id": str(i), "title": src["title"], "content": src["content"]}
            if "url" in src:
                entry["url"] = src["url"]
            cited.append(entry)
        for old, new in renum.items():
            ans = re.sub(rf"\[{old}\]", f"[{new}]", ans)
        logger.info("EvaluationModel invoked with user_query=%s", query)
        logger.info("EvaluationModel invoked with system_prompt=%s", self.DEFAULT_SYSTEM_PROMPT)
        logger.info("EvaluationModel invoked with model_response=%s", ans)
        logger.info("EvaluationModel invoked with sources/context=%s", context)
        logger.info("EvaluationModel invoked with user_query=%s", query)
        logger.info("EvaluationModel invoked with system_prompt=%s", self.DEFAULT_SYSTEM_PROMPT)
        logger.info("EvaluationModel invoked with model_response=%s", ans)
        logger.info("EvaluationModel invoked with sources/context=%s", context)
        eval = self.eval_model.evaluate(
            user_query=query,
            system_prompt=self.DEFAULT_SYSTEM_PROMPT,
            model_response=ans,
            sources=context
        )
        
        # ─── RESPONSE LOGGING ──────────────────────────────────────────────────────────────────
        logger.info("=" * 80)
        logger.info("Final Response and Sources")
        logger.info("=" * 80)
        logger.info(f"Query: {query}")
        logger.info(f"Answer: {ans}")
        logger.info(f"Cited Sources: {_json.dumps(cited, indent=2)}")
        logger.info(f"Context Used: {context}")
        logger.info("=" * 80)
        
        return ans, cited, [], eval, context

    def stream_rag_response(self, query: str) -> Generator[Union[str, Dict], None, None]:
        try:
            logger.info("========== START STREAM ==========")
            kb_results = self.search_knowledge_base(query)
            if not kb_results:
                yield "No relevant information found in the knowledge base."
                yield {"sources": [], "evaluation": {}}
                return
            context, src_map = self._prepare_context(kb_results)
            # Logging full context chunks before constructing stream messages
            for src_id, src_data in src_map.items():
                logger.info(f"=== Source {src_id}: {src_data['title']} ===")
                logger.info(src_data['content'])
            processed_system = self.DEFAULT_SYSTEM_PROMPT.strip()
            processed_user = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
            messages = [
                {"role": "system", "content": processed_system},
                {"role": "user", "content": processed_user}
            ]
            stream = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                stream=True
            )
            collected = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    piece = chunk.choices[0].delta.content
                    collected += piece
                    yield piece
            raw = self._filter_cited(collected, src_map)
            renum, cited = {}, []
            for i, src in enumerate(raw, 1):
                renum[src["id"]] = str(i)
                entry = {"id": str(i), "title": src["title"], "content": src["content"]}
                if "url" in src: entry["url"] = src["url"]
                cited.append(entry)
            for old, new in renum.items():
                collected = re.sub(rf"\[{old}\]", f"[{new}]", collected)
            logger.info("EvaluationModel invoked with user_query=%s", query)
            logger.info("EvaluationModel invoked with system_prompt=%s", self.DEFAULT_SYSTEM_PROMPT)
            logger.info("EvaluationModel invoked with model_response=%s", collected)
            logger.info("EvaluationModel invoked with sources/context=%s", context)
            eval = self.eval_model.evaluate(
                user_query=query,
                system_prompt=self.DEFAULT_SYSTEM_PROMPT,
                model_response=collected,
                sources=context
            )
            yield {"sources": cited, "evaluation": eval}
        except Exception as exc:
            logger.error("RAG stream error: %s", exc)
            yield "I encountered an error while streaming the response."
            yield {"sources": [], "evaluation": {}, "error": str(exc)}
