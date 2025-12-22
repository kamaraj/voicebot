"""
Async Guardrails Engine - Run guardrails in parallel without blocking LLM
Performance: 0ms blocking time (runs in background)
"""
import asyncio
from typing import Dict, Any
import structlog

from src.guardrails.engine import guardrails_engine
from src.config.settings import settings

logger = structlog.get_logger(__name__)


class AsyncGuardrailsEngine:
    """
    Async wrapper for guardrails that runs checks in parallel.
    Key benefit: ZERO blocking time for LLM responses!
    """
    
    def __init__(self):
        self.engine = guardrails_engine
        logger.info("async_guardrails_initialized", enabled=settings.guardrails_enabled)
    
    async def check_input_async(self, text: str) -> Dict[str, Any]:
        """
        Run input guardrails in background thread.
        This doesn't block the event loop!
        
        Returns immediately, logs violations asynchronously.
        """
        if not settings.guardrails_enabled:
            return {"status": "disabled", "passed": True}
        
        try:
            # Run blocking guardrails in executor (background thread)
            result = await asyncio.to_thread(
                self.engine.check_input,
                text
            )
            
            # Check if all passed
            all_passed = all(check.passed for check in result.values())
            
            if not all_passed:
                # Log violations (doesn't block user response!)
                violations = [
                    {
                        "check": check_name,
                        "violations": check.violations
                    }
                    for check_name, check in result.items()
                    if not check.passed
                ]
                
                logger.warning(
                    "guardrails_violations_detected",
                    violations=violations,
                    text_preview=text[:100]
                )
            
            return {
                "status": "checked",
                "passed": all_passed,
                "results": result
            }
            
        except Exception as e:
            logger.error(
                "guardrails_check_error",
                error=str(e),
                error_type=type(e).__name__
            )
            # Fail open - don't block user on guardrails error
            return {"status": "error", "passed": True, "error": str(e)}
    
    async def check_output_async(self, text: str) -> Dict[str, Any]:
        """
        Run output guardrails in background thread.
        Similar to input check but for LLM responses.
        """
        if not settings.guardrails_enabled:
            return {"status": "disabled", "passed": True}
        
        try:
            result = await asyncio.to_thread(
                self.engine.check_output,
                text
            )
            
            all_passed = all(check.passed for check in result.values())
            
            if not all_passed:
                logger.warning(
                    "output_guardrails_violations",
                    violations=[
                        check.violations
                        for check in result.values()
                        if not check.passed
                    ]
                )
            
            return {
                "status": "checked",
                "passed": all_passed,
                "results": result
            }
            
        except Exception as e:
            logger.error("output_guardrails_error", error=str(e))
            return {"status": "error", "passed": True, "error": str(e)}
    
    async def check_parallel(self, user_message: str, run_async: bool = True):
        """
        Check guardrails in parallel with LLM processing.
        
        Usage:
            # Start guardrails check (don't wait!)
            guard_task = engine.check_parallel(message)
            
            # Process with LLM immediately
            response = await llm.generate(message)
            
            # Optionally wait for guardrails result later
            guard_result = await guard_task
        
        Args:
            user_message: Message to check
            run_async: If True, starts task and returns immediately
                      If False, waits for result
        
        Returns:
            Coroutine/Task if async, result if sync
        """
        check_task = asyncio.create_task(
            self.check_input_async(user_message)
        )
        
        if run_async:
            # Return task immediately (caller can await later or ignore)
            return check_task
        else:
            # Wait for result
            return await check_task


# Global async engine instance
async_guardrails = AsyncGuardrailsEngine()
