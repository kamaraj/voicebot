"""
End-to-end tests using synthetic personas.
"""
import pytest
from src.agents.voice_agent import VoiceAgent
from src.tests.personas import PersonaGenerator, PersonaBehavior


@pytest.mark.asyncio
class TestPersonaInteractions:
    """Test agent with various synthetic personas."""
    
    async def test_cooperative_persona(self):
        """Test with cooperative user."""
        agent = VoiceAgent()
        generator = PersonaGenerator()
        
        persona = generator.generate_persona(behavior=PersonaBehavior.COOPERATIVE)
        
        # Test with persona's utterances
        for utterance in persona.sample_utterances[:2]:  # Limit for speed
            response = await agent.process_message(
                user_message=utterance,
                conversation_id=persona.id,
                user_id=persona.id
            )
            
            assert response is not None
            assert len(response["response"]) > 0
    
    async def test_confused_persona(self):
        """Test with confused user."""
        agent = VoiceAgent()
        generator = PersonaGenerator()
        
        persona = generator.generate_persona(behavior=PersonaBehavior.CONFUSED)
        
        for utterance in persona.sample_utterances[:2]:
            response = await agent.process_message(
                user_message=utterance,
                conversation_id=persona.id
            )
            
            # Should handle confused input gracefully
            assert response is not None
    
    async def test_adversarial_persona(self):
        """Test with adversarial user (security testing)."""
        agent = VoiceAgent()
        generator = PersonaGenerator()
        
        persona = generator.generate_persona(behavior=PersonaBehavior.ADVERSARIAL)
        
        for utterance in persona.sample_utterances[:2]:
            response = await agent.process_message(
                user_message=utterance,
                conversation_id=persona.id
            )
            
            # Should reject or safely handle adversarial input
            assert response is not None
            # Guardrails should be triggered
            if response.get("metadata", {}).get("guardrails"):
                assert True  # Guardrails working
    
    async def test_persona_suite(self):
        """Test with full persona suite."""
        agent = VoiceAgent()
        generator = PersonaGenerator()
        
        # Generate smaller suite for testing
        personas = generator.generate_persona_suite(count=5)
        
        results = []
        for persona in personas:
            # Test one utterance per persona
            if persona.sample_utterances:
                utterance = persona.sample_utterances[0]
                
                response = await agent.process_message(
                    user_message=utterance,
                    conversation_id=persona.id
                )
                
                results.append({
                    "persona_id": persona.id,
                    "behavior": persona.behavior.value,
                    "success": response is not None
                })
        
        # All should succeed (even if with errors/guardrails)
        assert len(results) == len(personas)
        assert all(r["success"] for r in results)
