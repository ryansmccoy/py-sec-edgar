"""Example: Using GenAI Spine Client from Capture-Spine.

This shows how capture-spine (or any consumer app) would use the
GenAI Spine client to offload LLM operations.

The GenAI Spine service runs in Docker. This client just makes HTTP calls.
"""

import asyncio
from uuid import UUID

# Import the client (copy to your app or use local path install)
from genai_spine_client import GenAIClient, NotFoundError, ProviderError


async def example_chat_completion():
    """Simple chat completion - OpenAI compatible."""
    async with GenAIClient(base_url="http://localhost:8100") as client:
        # Basic completion
        response = await client.chat_complete(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
            ],
            model="gpt-4o-mini",
            temperature=0.7,
        )

        print(f"Response: {response.content}")
        print(f"Tokens: {response.usage.total_tokens}")


async def example_execute_prompt():
    """Execute a saved prompt with variables."""
    async with GenAIClient(base_url="http://localhost:8100") as client:
        # First, create a prompt (or use existing one)
        try:
            prompt = await client.get_prompt("summarizer")
        except NotFoundError:
            prompt = await client.create_prompt(
                name="Text Summarizer",
                slug="summarizer",
                user_prompt_template="Summarize the following text in {format} format:\n\n{text}",
                description="Summarizes text in various formats",
                variables=[
                    {"name": "text", "type": "string", "required": True},
                    {"name": "format", "type": "string", "default": "bullets"},
                ],
            )
            print(f"Created prompt: {prompt.slug}")

        # Execute the prompt
        result = await client.execute_prompt(
            slug="summarizer",
            variables={
                "text": """
                Python is a high-level, general-purpose programming language.
                Its design philosophy emphasizes code readability with the use
                of significant indentation. Python is dynamically typed and
                garbage-collected. It supports multiple programming paradigms,
                including structured, object-oriented and functional programming.
                """,
                "format": "bullets",
            },
        )

        print(f"Summary:\n{result.output}")
        print(f"Cost: ${result.cost_usd:.4f}")


async def example_chat_session():
    """Stateful chat session with history.

    This is how capture-spine's chat feature would work.
    """
    async with GenAIClient(base_url="http://localhost:8100") as client:
        # Create a session (history is maintained automatically)
        session = await client.create_session(
            model="gpt-4o-mini",
            system_prompt="You are a helpful coding assistant.",
            metadata={
                "app": "capture-spine",
                "user_id": "user_123",
                "feature": "chat",
            },
        )
        print(f"Created session: {session.id}")

        # Send messages - context is preserved
        reply1 = await client.send_message(
            session_id=session.id,
            content="What's the difference between a list and a tuple in Python?",
        )
        print(f"\nUser: What's the difference between a list and a tuple in Python?")
        print(f"Assistant: {reply1.content[:200]}...")

        # Follow-up question - session remembers the context
        reply2 = await client.send_message(
            session_id=session.id,
            content="Which one should I use for storing coordinates?",
        )
        print(f"\nUser: Which one should I use for storing coordinates?")
        print(f"Assistant: {reply2.content[:200]}...")

        # Get session stats
        session_info = await client.get_session(session.id)
        print(f"\nSession stats:")
        print(f"  Messages: {session_info.message_count}")
        print(f"  Total tokens: {session_info.total_tokens}")
        print(f"  Total cost: ${session_info.total_cost_usd:.4f}")


async def example_capture_spine_integration():
    """How capture-spine's LLM Transform feature would use GenAI Spine.

    Instead of calling LLM providers directly, capture-spine calls GenAI Spine.
    Domain logic stays in capture-spine; LLM execution is in GenAI Spine.
    """
    async with GenAIClient(base_url="http://localhost:8100") as client:
        # capture-spine has the domain context
        message_content = """
        hey can u help me with this code?? its not working lol

        def foo(x):
            return x+1
        """
        enrichment_mode = "professional"  # capture-spine decides this

        # Create the enrichment prompt if it doesn't exist
        try:
            await client.get_prompt("message-enricher")
        except NotFoundError:
            await client.create_prompt(
                name="Message Enricher",
                slug="message-enricher",
                system_prompt="You are a professional writing assistant.",
                user_prompt_template="""Rewrite the following message to be more {mode}.
Preserve the technical content and code blocks.
Only output the rewritten message, nothing else.

Message:
{content}""",
                variables=[
                    {"name": "content", "type": "string", "required": True},
                    {"name": "mode", "type": "string", "default": "professional"},
                ],
            )

        # capture-spine calls GenAI Spine with domain context
        result = await client.execute_prompt(
            slug="message-enricher",
            variables={
                "content": message_content,
                "mode": enrichment_mode,
            },
        )

        print("Original message:")
        print(message_content)
        print("\nEnriched message:")
        print(result.output)


async def example_error_handling():
    """Proper error handling with the client."""
    async with GenAIClient(base_url="http://localhost:8100") as client:
        try:
            # Try to execute a prompt that doesn't exist
            result = await client.execute_prompt(
                slug="nonexistent-prompt",
                variables={"text": "Hello"},
            )
        except NotFoundError as e:
            print(f"Prompt not found: {e.message}")
            print(f"Request ID: {e.request_id}")

        try:
            # Simulate a provider error
            result = await client.chat_complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="nonexistent-model",
            )
        except ProviderError as e:
            print(f"Provider error: {e.message}")
            if e.is_retryable:
                print("This error is retryable")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Example 1: Chat Completion")
    print("=" * 60)
    try:
        await example_chat_completion()
    except Exception as e:
        print(f"Skipped (GenAI Spine not running): {e}")

    print("\n" + "=" * 60)
    print("Example 2: Execute Prompt")
    print("=" * 60)
    try:
        await example_execute_prompt()
    except Exception as e:
        print(f"Skipped (GenAI Spine not running): {e}")

    print("\n" + "=" * 60)
    print("Example 3: Chat Session")
    print("=" * 60)
    try:
        await example_chat_session()
    except Exception as e:
        print(f"Skipped (GenAI Spine not running): {e}")

    print("\n" + "=" * 60)
    print("Example 4: Capture-Spine Integration")
    print("=" * 60)
    try:
        await example_capture_spine_integration()
    except Exception as e:
        print(f"Skipped (GenAI Spine not running): {e}")


if __name__ == "__main__":
    asyncio.run(main())
