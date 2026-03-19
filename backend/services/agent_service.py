"""
Agent Service for text corrections using Azure OpenAI via APIM.

This service integrates with Azure OpenAI GPT-4o through Azure API Management
to provide streaming text correction suggestions.
"""

import logging
import json
from typing import AsyncGenerator, Dict, Any
from dotenv import load_dotenv

from openai import AsyncAzureOpenAI

from config import settings

# Load environment variables (override=False so runtime vars take precedence)
load_dotenv(override=False)

logger = logging.getLogger(__name__)


# System prompt for text correction
CORRECTION_SYSTEM_PROMPT = """You are an expert text correction assistant. Your role is to analyze text and provide corrections for:

1. **Grammar**: Fix grammatical errors while preserving the author's intent
2. **Spelling**: Correct spelling mistakes
3. **Style**: Improve sentence structure and clarity
4. **Tone**: Suggest tone improvements when appropriate
5. **Rephrasing**: Offer better phrasing options

When analyzing text, provide your corrections in a structured JSON format with the following schema:
{
    "corrections": [
        {
            "type": "grammar|spelling|style|tone|rephrasing",
            "original_text": "the text to be corrected",
            "suggested_text": "the corrected version",
            "explanation": "brief explanation of the correction",
            "start_position": 0,
            "end_position": 10
        }
    ]
}

Be concise, helpful, and accurate. Focus on meaningful improvements.
"""


class AgentService:
    """Service for managing AI agent interactions with Azure OpenAI via APIM."""

    def __init__(self):
        """Initialize the agent service with Azure OpenAI APIM configuration."""
        self.azure_endpoint = settings.azure_openai_endpoint
        self.deployment_name = settings.azure_openai_deployment_name
        self.api_version = settings.azure_openai_api_version
        self.api_key = settings.azure_openai_api_key

        # Initialize Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

        logger.info(
            "Initialized AgentService with APIM endpoint: %s", self.azure_endpoint
        )
        logger.info("Model deployment: %s", self.deployment_name)

    async def validate_connection(self) -> bool:
        """
        Validate connection to Azure OpenAI via APIM.

        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {
                        "role": "user",
                        "content": "Respond with OK to confirm connection.",
                    },
                ],
                max_tokens=10,
            )

            if response and response.choices:
                logger.info("Azure OpenAI (APIM) connection validated successfully")
                return True
            return False
        except Exception as e:
            logger.error("Azure OpenAI (APIM) connection validation failed: %s", str(e))
            return False

    async def stream_corrections(
        self, text: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream text correction suggestions from Foundry GPT-4o model.

        This method creates an AI agent that analyzes the input text and streams
        correction suggestions in real-time.Azure OpenAI GPT-4o via APIM.

        This method calls Azure OpenAI through APIM and streams
        correction suggestions in real-time.

        Args:
            text: The text to analyze and correct

        Yields:
            Dict containing correction chunks with type, original_text, suggested_text, etc.

        Raises:
            Exception: If API call or streaming fails
        """
        try:
            logger.info(
                "Creating text correction request for text length: %d", len(text)
            )

            # Build correction request prompt
            user_prompt = f"""Please analyze the following text and provide corrections:

TEXT TO ANALYZE:
{text}

Provide your response in the structured JSON format specified in your instructions."""

            logger.info("Starting streaming response from Azure OpenAI (APIM)...")

            # Stream response using Azure OpenAI client
            stream = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": CORRECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                max_tokens=2000,
                temperature=0.7,
            )

            chunk_count = 0
            full_content = ""

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta

                    if delta.content:
                        chunk_count += 1
                        content = delta.content
                        full_content += content

                        yield {
                            "type": "chunk",
                            "content": content,
                            "chunk_number": chunk_count,
                        }

            logger.info("Streaming completed. Total chunks: %d", chunk_count)

            # Parse and validate the JSON response
            try:
                # Try to extract JSON from the response (handles markdown code blocks)
                json_content = self._extract_json(full_content)
                parsed_response = json.loads(json_content)

                # Validate that it has the expected structure
                if "corrections" not in parsed_response:
                    logger.warning(
                        "Response missing 'corrections' field, wrapping in structure"
                    )
                    # If GPT-4o returned just an array, wrap it
                    if isinstance(parsed_response, list):
                        parsed_response = {"corrections": parsed_response}
                    else:
                        parsed_response = {"corrections": []}

                logger.info(
                    "Parsed %d corrections",
                    len(parsed_response.get("corrections", [])),
                )

                # Yield final indicator with parsed content
                yield {
                    "type": "complete",
                    "total_chunks": chunk_count,
                    "content": json.dumps(parsed_response),
                }
            except json.JSONDecodeError as parse_error:
                logger.error("Failed to parse JSON response: %s", parse_error)
                logger.error("Raw content: %s", full_content[:500])
                # Yield error but include raw content for debugging
                yield {
                    "type": "error",
                    "error": "Invalid JSON response from model",
                    "message": f"Failed to parse model response. Raw content: {full_content[:200]}",
                }

        except Exception as e:
            logger.error("Error in stream_corrections: %s", str(e), exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "message": "Failed to stream corrections from Azure OpenAI (APIM)",
            }

    def _extract_json(self, content: str) -> str:
        """
        Extract JSON from content that might be wrapped in markdown code blocks.

        Args:
            content: Raw content possibly containing JSON

        Returns:
            Extracted JSON string
        """
        # Remove markdown code blocks if present
        import re

        # Try to find JSON in markdown code blocks
        json_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(json_block_pattern, content, re.DOTALL)
        if match:
            return match.group(1)

        # Try to find raw JSON object
        json_pattern = r"\{.*\}"
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            return match.group(0)

        # Return as-is if no pattern matches
        return content.strip()


# Global instance
_agent_service_instance: AgentService = None


def get_agent_service() -> AgentService:
    """
    Get or create the global AgentService instance.

    Returns:
        AgentService: Singleton agent service instance
    """
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance
