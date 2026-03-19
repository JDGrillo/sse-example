"""
Corrections API routes for streaming text corrections.
"""

import logging
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from services import get_agent_service
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/corrections", tags=["corrections"])


class CorrectionRequest(BaseModel):
    """Request model for text correction."""

    text: str = Field(..., min_length=1, description="Text to analyze and correct")
    request_id: Optional[str] = Field(
        None, description="Optional request ID for tracking"
    )

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Validate text length doesn't exceed maximum."""
        if len(v) > settings.max_text_length:
            raise ValueError(
                f"Text length ({len(v)}) exceeds maximum allowed length "
                f"({settings.max_text_length})"
            )
        return v


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    agent_service: str


@router.get("/health", response_model=HealthResponse)
async def corrections_health():
    """
    Health check endpoint for corrections service.

    Returns:
        HealthResponse: Service health status
    """
    # TODO: Add actual agent service health check
    return HealthResponse(status="healthy", agent_service="ready")


async def generate_sse_stream(text: str, request_id: Optional[str] = None):
    """
    Generate Server-Sent Events stream for text corrections.

    Args:
        text: Text to analyze and correct
        request_id: Optional request ID for tracking

    Yields:
        str: Server-Sent Event formatted messages
    """
    agent_service = get_agent_service()

    try:
        logger.info(
            "Starting streaming corrections for request_id=%s, text_length=%d",
            request_id or "unknown",
            len(text),
        )

        # Send initial event
        yield f"event: start\ndata: {json.dumps({'request_id': request_id, 'status': 'streaming'})}\n\n"

        # Stream corrections from agent service
        async for chunk in agent_service.stream_corrections(text):
            # Format as Server-Sent Event
            chunk_type = chunk.get("type", "chunk")

            if chunk_type == "chunk":
                # Send content chunk
                event_data = {
                    "type": "chunk",
                    "content": chunk.get("content", ""),
                    "chunk_number": chunk.get("chunk_number", 0),
                }
                yield f"event: chunk\ndata: {json.dumps(event_data)}\n\n"

            elif chunk_type == "complete":
                # Send completion event with full content
                event_data = {
                    "type": "complete",
                    "total_chunks": chunk.get("total_chunks", 0),
                    "content": chunk.get(
                        "content", ""
                    ),  # Include the parsed corrections JSON
                    "request_id": request_id,
                }
                yield f"event: complete\ndata: {json.dumps(event_data)}\n\n"
                logger.info(
                    "Completed streaming corrections for request_id=%s",
                    request_id or "unknown",
                )

            elif chunk_type == "error":
                # Send error event
                event_data = {
                    "type": "error",
                    "error": chunk.get("error", "Unknown error"),
                    "message": chunk.get("message", ""),
                }
                yield f"event: error\ndata: {json.dumps(event_data)}\n\n"
                logger.error(
                    "Error in streaming corrections for request_id=%s: %s",
                    request_id or "unknown",
                    chunk.get("error"),
                )

    except Exception as e:
        logger.error(
            "Unexpected error in generate_sse_stream for request_id=%s: %s",
            request_id or "unknown",
            str(e),
            exc_info=True,
        )
        error_data = {
            "type": "error",
            "error": str(e),
            "message": "Failed to stream corrections",
        }
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    finally:
        # Send final close event
        yield f"event: close\ndata: {json.dumps({'request_id': request_id})}\n\n"


@router.post("/stream")
async def stream_corrections(request: Request, correction_request: CorrectionRequest):
    """
    Stream text correction suggestions using Server-Sent Events.

    This endpoint analyzes the provided text and streams correction suggestions
    in real-time using Microsoft Foundry GPT-4o via the Agent Framework SDK.

    Args:
        request: FastAPI request object for connection monitoring
        correction_request: The correction request containing text to analyze

    Returns:
        StreamingResponse: Server-Sent Events stream with corrections

    Raises:
        HTTPException: If request validation fails or service unavailable
    """
    text = correction_request.text
    request_id = correction_request.request_id

    logger.info(
        "Received correction request: request_id=%s, text_length=%d",
        request_id or "unknown",
        len(text),
    )

    # Check if client is still connected before starting expensive operation
    if await request.is_disconnected():
        logger.warning(
            "Client disconnected before streaming started: request_id=%s",
            request_id or "unknown",
        )
        raise HTTPException(status_code=499, detail="Client Closed Request")

    try:
        return StreamingResponse(
            generate_sse_stream(text, request_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )
    except ValueError as e:
        # Validation errors (e.g., text too long)
        logger.warning("Validation error in stream_corrections: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating streaming response: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to initiate correction streaming"
        )
