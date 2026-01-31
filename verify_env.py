
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.engine.llm_client import LLMClient

async def main():
    # Load environment variables
    load_dotenv()
    
    # Check if API key is loaded
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in environment variables.")
        return
    else:
        print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")

    print("🔄 Initializing LLM Client...")
    try:
        client = LLMClient()
        print(f"   Model: {client.model}")
        print(f"   API URL: {client.api_url}")
    except Exception as e:
        print(f"❌ Error initializing client: {e}")
        return

    print("🚀 Sending test request to OpenRouter...")
    try:
        response = await client.generate(
            prompt="Hello, are you functional? Respond with 'Yes'.", 
            system_prompt="You are a test script helper."
        )
        print("\n✅ Success! Response from AI:")
        print("-" * 20)
        print(response)
        print("-" * 20)
    except Exception as e:
        print(f"\n❌ API Request Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
