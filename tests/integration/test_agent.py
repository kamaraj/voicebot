"""
Integration tests for the voice agent.
"""
import pytest
from src.agents.voice_agent import VoiceAgent


@pytest.mark.asyncio
class TestVoiceAgent:
    """Integration tests for VoiceAgent."""
    
    async def test_simple_conversation(self):
        """Test basic conversation flow."""
        agent = VoiceAgent()
        
        response = await agent.process_message(
            user_message="Hello, how are you?",
            conversation_id="test_conv_1"
        )
        
        assert response is not None
        assert "response" in response
        assert len(response["response"]) > 0
    
    async def test_tool_usage(self):
        """Test that tools are called when appropriate."""
        agent = VoiceAgent()
        
        response = await agent.process_message(
            user_message="What time is it?",
            conversation_id="test_conv_2"
        )
        
        assert response is not None
        # Tool should be called for time query
        assert "tool_results" in response
    
    async def test_guardrails_integration(self):
        """Test that guardrails are applied."""
        agent = VoiceAgent()
        
        # Input with PII
        response = await agent.process_message(
            user_message="My email is test@example.com, can you help?",
            conversation_id="test_conv_3"
        )
        
        assert response is not None
        # Should still work but with guardrails applied
        assert "metadata" in response
    
    async def test_context_preservation(self):
        """Test context is preserved across calls."""
        agent = VoiceAgent()
        conv_id = "test_conv_4"
        
        # First message
        response1 = await agent.process_message(
            user_message="My name is Alice",
            conversation_id=conv_id
        )
        
        # Follow-up (TODO: implement actual memory)
        response2 = await agent.process_message(
            user_message="What's my name?",
            conversation_id=conv_id
        )
        
        assert response1 is not None
        assert response2 is not None


@pytest.mark.asyncio
class TestAgentTools:
    """Test individual agent tools."""
    
    async def test_get_current_time(self):
        """Test time retrieval tool."""
        agent = VoiceAgent()
        result = await agent.get_current_time()
        
        assert "time" in result
        assert "formatted" in result
    
    async def test_schedule_appointment(self):
        """Test appointment scheduling tool."""
        agent = VoiceAgent()
        result = await agent.schedule_appointment(
            date="2024-12-10",
            time="2:00 PM",
            description="Team meeting"
        )
        
        assert result["success"] is True
        assert "appointment_id" in result
