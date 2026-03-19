"""
Test Azure OpenAI connection via APIM with the exact endpoint format from portal.

This script tests the APIM endpoint configuration to ensure it matches the portal test format:
POST https://jdsaiapim.azure-api.net/gpt-4o/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

load_dotenv()


async def test_apim_connection():
    """Test connection to Azure OpenAI via APIM."""

    # Get configuration
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    print("=" * 70)
    print("Azure OpenAI APIM Connection Test")
    print("=" * 70)
    print(f"Endpoint:    {endpoint}")
    print(f"Deployment:  {deployment}")
    print(f"API Version: {api_version}")
    print(
        f"API Key:     {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'NOT SET'}"
    )
    print("=" * 70)

    if not all([endpoint, deployment, api_version, api_key]):
        print("\n❌ ERROR: Missing required environment variables")
        print(
            "Please set: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_KEY"
        )
        return False

    try:
        # Initialize client
        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

        print("\n✓ Client initialized successfully")
        print(
            f"\nSending test request to: {endpoint}/openai/deployments/{deployment}/chat/completions"
        )
        print(
            "Request:",
            {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "How are you?"},
                ],
                "max_tokens": 50,
            },
        )

        # Test connection with exact message from portal
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "How are you?"},
            ],
            max_tokens=50,
        )

        print("\n" + "=" * 70)
        print("✅ SUCCESS! Connection to APIM works correctly")
        print("=" * 70)
        print(f"\nResponse:")
        print(f"  Model: {response.model}")
        print(f"  Content: {response.choices[0].message.content}")
        print(
            f"  Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}"
        )
        print("\n✓ Your local environment is configured correctly!")
        print("✓ The endpoint format matches the APIM portal test")

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ ERROR: Connection failed")
        print("=" * 70)
        print(f"\nError type: {type(e).__name__}")
        print(f"Error message: {str(e)}")

        # Provide helpful troubleshooting
        print("\n🔧 Troubleshooting:")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("  - Check your AZURE_OPENAI_API_KEY (subscription key from APIM)")
            print("  - In Azure portal, go to APIM → Subscriptions → copy the key")
        elif "404" in str(e):
            print("  - Verify AZURE_OPENAI_ENDPOINT is correct")
            print("  - Verify AZURE_OPENAI_DEPLOYMENT_NAME matches your deployment")
        elif "SSL" in str(e) or "certificate" in str(e):
            print("  - Check your network/firewall settings")
            print("  - Verify HTTPS is working")
        else:
            print("  - Verify all environment variables in .env are correct")
            print("  - Check APIM is properly configured and accessible")

        return False


async def test_streaming():
    """Test streaming response."""

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    print("\n" + "=" * 70)
    print("Testing Streaming Response")
    print("=" * 70)

    try:
        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

        print("\nSending streaming request...")

        stream = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "Count from 1 to 5, one number per line."}
            ],
            stream=True,
            max_tokens=100,
        )

        print("\nStreaming response:")
        chunk_count = 0
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                chunk_count += 1

        print(f"\n\n✅ Streaming works! Received {chunk_count} chunks")
        return True

    except Exception as e:
        print(f"\n❌ Streaming test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("AZURE OPENAI APIM CONFIGURATION TEST")
    print("=" * 70)

    # Test basic connection
    basic_success = await test_apim_connection()

    if basic_success:
        # Test streaming
        await test_streaming()

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
