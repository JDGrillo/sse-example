"""
Test script for Agent Service Foundry integration.

This script validates the connection to Microsoft Foundry and tests
streaming corrections functionality.
"""

import asyncio
import sys
import logging

from services.agent_service import get_agent_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test Foundry connection."""
    logger.info("=" * 60)
    logger.info("Testing Foundry Connection")
    logger.info("=" * 60)

    agent_service = get_agent_service()

    is_valid = await agent_service.validate_connection()

    if is_valid:
        logger.info("✓ Connection test PASSED")
        return True
    else:
        logger.error("✗ Connection test FAILED")
        return False


async def test_streaming_corrections():
    """Test streaming corrections with sample text."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Streaming Corrections")
    logger.info("=" * 60)

    # Sample text with deliberate errors
    sample_text = """This is a sample txt with some erors. The grammer is not perfekt 
    and there might be some style issues too. Lets see what corrections the AI can provide."""

    logger.info(f"\nInput text ({len(sample_text)} chars):")
    logger.info(f"  {sample_text[:100]}...")

    agent_service = get_agent_service()

    try:
        logger.info("\nStreaming corrections...")
        chunks_received = 0

        async for chunk in agent_service.stream_corrections(sample_text):
            chunks_received += 1

            if chunk.get("type") == "chunk":
                # Print chunk content inline
                print(chunk.get("content", ""), end="", flush=True)
            elif chunk.get("type") == "complete":
                print("\n")  # New line after completion
                logger.info(
                    f"\n✓ Streaming completed. Total chunks: {chunk.get('total_chunks')}"
                )
            elif chunk.get("type") == "error":
                logger.error(f"\n✗ Error: {chunk.get('error')}")
                return False

        if chunks_received > 0:
            logger.info("✓ Streaming test PASSED")
            return True
        else:
            logger.warning("⚠ No chunks received")
            return False

    except Exception as e:
        logger.error(f"✗ Streaming test FAILED: {str(e)}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("Agent Service Test Suite")
    logger.info("=" * 60)

    # Test 1: Connection
    connection_ok = await test_connection()

    if not connection_ok:
        logger.error("\n⚠ Skipping streaming test due to connection failure")
        logger.error("\nPlease ensure:")
        logger.error("  1. FOUNDRY_PROJECT_ENDPOINT is set in .env")
        logger.error("  2. FOUNDRY_MODEL_DEPLOYMENT_NAME is set in .env")
        logger.error(
            "  3. Azure credentials are configured (az login or DefaultAzureCredential)"
        )
        logger.error("  4. You have access to the Foundry project")
        sys.exit(1)

    # Test 2: Streaming
    streaming_ok = await test_streaming_corrections()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info(f"  Connection:        {'✓ PASS' if connection_ok else '✗ FAIL'}")
    logger.info(f"  Streaming:         {'✓ PASS' if streaming_ok else '✗ FAIL'}")
    logger.info("=" * 60)

    if connection_ok and streaming_ok:
        logger.info("\n✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("\n✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
