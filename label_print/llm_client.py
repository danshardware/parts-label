"""LLM client for label processing using AWS Bedrock Nova Lite."""

import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO

from PIL import Image
import boto3

from .prompts import (
    LABEL_EXTRACTION_PROMPT,
    LABEL_CLEANUP_PROMPT,
    COMPONENT_MATCH_VERIFICATION_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for AWS Bedrock Nova Lite operations."""

    def __init__(self, model_id: str = "us.amazon.nova-lite-v1:0", region: str = "us-east-1"):
        """
        Initialize LLM client.

        Args:
            model_id: AWS Bedrock model ID (default: Nova Lite)
            region: AWS region for Bedrock
        """
        self.model_id = model_id
        self.bedrock = boto3.client("bedrock-runtime", region_name=region)

    def extract_label_data(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract component data from label image.

        Args:
            image_path: Path to label image

        Returns:
            Dictionary with extracted label data
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Call Nova Lite with vision
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": {
                                    "format": "jpeg",
                                    "source": {"bytes": image_data}
                                }
                            },
                            {"text": LABEL_EXTRACTION_PROMPT}
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 1000,
                    "temperature": 0.0
                }
            }

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            content = response_body.get("output", {}).get("message", {}).get("content", [])

            if content and len(content) > 0:
                text = content[0].get("text", "")
            else:
                logger.error("No content in LLM response")
                return {"error": "No content in response"}

            # Extract JSON
            text = self._extract_json_from_response(text)
            result = json.loads(text)

            logger.info(f"Extracted label data: {result.get('manufacturer_pn', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Failed to extract label data: {e}")
            return {"error": str(e)}

    def cleanup_label_text(
        self, manufacturer_pn: str, raw_description: str
    ) -> Dict[str, str]:
        """
        Clean up component description for label printing.

        Args:
            manufacturer_pn: Manufacturer part number
            raw_description: Raw description from label/lookup

        Returns:
            Dictionary with 'title' and 'description' keys
        """
        try:
            prompt = LABEL_CLEANUP_PROMPT.format(
                manufacturer_pn=manufacturer_pn,
                raw_description=raw_description,
            )

            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 500,
                    "temperature": 0.0
                }
            }

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            content = response_body.get("output", {}).get("message", {}).get("content", [])

            if content and len(content) > 0:
                text = content[0].get("text", "")
            else:
                logger.error("No content in cleanup response")
                return {
                    "title": manufacturer_pn[:20],
                    "description": raw_description[:50],
                }

            # Extract JSON
            text = self._extract_json_from_response(text)
            result = json.loads(text)

            logger.info(f"Cleaned up label: {result.get('title', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"Failed to cleanup label text: {e}")
            # Fallback to original data
            return {
                "title": manufacturer_pn[:20],
                "description": raw_description[:50],
            }

    def verify_component_match(
        self,
        pn_a: str,
        desc_a: str,
        pn_b: str,
        desc_b: str,
    ) -> Dict[str, Any]:
        """
        Verify if two components are the same part.

        Args:
            pn_a: Part number A
            desc_a: Description A
            pn_b: Part number B
            desc_b: Description B

        Returns:
            Dictionary with 'match', 'confidence', 'reason'
        """
        try:
            prompt = COMPONENT_MATCH_VERIFICATION_PROMPT.format(
                pn_a=pn_a,
                desc_a=desc_a,
                pn_b=pn_b,
                desc_b=desc_b,
            )

            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 300,
                    "temperature": 0.0
                }
            }

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            content = response_body.get("output", {}).get("message", {}).get("content", [])

            if content and len(content) > 0:
                text = content[0].get("text", "")
            else:
                logger.error("No content in verification response")
                return {"match": False, "confidence": "low", "reason": "No response"}

            # Extract JSON
            text = self._extract_json_from_response(text)
            result = json.loads(text)

            logger.info(f"Match verification: {result.get('match', False)}")
            return result

        except Exception as e:
            logger.error(f"Failed to verify component match: {e}")
            return {"match": False, "confidence": "low", "reason": str(e)}

    def _extract_json_from_response(self, text: str) -> str:
        """
        Extract JSON from LLM response (handles markdown code blocks).

        Args:
            text: Raw LLM response text

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return text
