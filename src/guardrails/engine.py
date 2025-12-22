"""
AI Guardrails for safety, security, and quality control.
Implements PII detection, toxicity filtering, prompt injection prevention.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
import re
import structlog

# Optional presidio imports - only needed if PII detection is enabled
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    AnalyzerEngine = None
    AnonymizerEngine = None

from src.config.settings import settings
from src.observability.metrics import metrics

logger = structlog.get_logger(__name__)


class ViolationSeverity(Enum):
    """Severity levels for guardrail violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailResult:
    """Result from guardrail check."""
    
    def __init__(
        self,
        passed: bool,
        violations: List[Dict[str, Any]] = None,
        sanitized_text: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.passed = passed
        self.violations = violations or []
        self.sanitized_text = sanitized_text
        self.metadata = metadata or {}


class PIIGuardrail:
    """
    Detects and redacts Personally Identifiable Information (PII).
    Uses Microsoft Presidio for enterprise-grade PII detection.
    """
    
    def __init__(self):
        if not PRESIDIO_AVAILABLE:
            raise ImportError("presidio_analyzer and presidio_anonymizer are required for PII detection")
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # PII entities to detect
        self.entities = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "LOCATION",
            "DATE_TIME",
            "US_SSN",
            "US_DRIVER_LICENSE",
            "US_PASSPORT"
        ]
        
        logger.info("pii_guardrail_initialized", entities=self.entities)
    
    def check(self, text: str, language: str = "en") -> GuardrailResult:
        """
        Detect PII in text.
        
        Args:
            text: Input text to check
            language: Language code
            
        Returns:
            GuardrailResult with violations and sanitized text
        """
        try:
            # Analyze for PII
            results = self.analyzer.analyze(
                text=text,
                entities=self.entities,
                language=language
            )
            
            violations = []
            for result in results:
                violations.append({
                    "type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                })
            
            # Anonymize if violations found
            sanitized_text = None
            if violations:
                anonymized = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=results
                )
                sanitized_text = anonymized.text
            
            passed = len(violations) == 0
            
            # Track metrics
            metrics.track_guardrail(
                check_type="pii_detection",
                result="pass" if passed else "fail",
                violation=not passed,
                severity="high" if violations else "low"
            )
            
            logger.info(
                "pii_check_completed",
                violations_count=len(violations),
                passed=passed
            )
            
            return GuardrailResult(
                passed=passed,
                violations=violations,
                sanitized_text=sanitized_text,
                metadata={"check_type": "pii", "language": language}
            )
            
        except Exception as e:
            logger.error("pii_check_failed", error=str(e))
            return GuardrailResult(passed=True)  # Fail open


class ToxicityGuardrail:
    """
    Detects toxic, harmful, or inappropriate content.
    Uses pattern matching and keyword detection.
    """
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        
        # Toxic patterns (simplified - use ML model in production)
        self.toxic_patterns = [
            r'\b(hate|kill|die|stupid|idiot|damn)\b',
            r'\b(racist|sexist|bigot)\b',
        ]
        
        logger.info("toxicity_guardrail_initialized", threshold=threshold)
    
    def check(self, text: str) -> GuardrailResult:
        """
        Check for toxic content.
        
        Args:
            text: Input text to check
            
        Returns:
            GuardrailResult
        """
        violations = []
        
        # Check patterns
        for pattern in self.toxic_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                violations.append({
                    "type": "toxicity",
                    "pattern": pattern,
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        passed = len(violations) == 0
        
        # Track metrics
        metrics.track_guardrail(
            check_type="toxicity",
            result="pass" if passed else "fail",
            violation=not passed,
            severity="medium" if violations else "low"
        )
        
        return GuardrailResult(
            passed=passed,
            violations=violations,
            metadata={"check_type": "toxicity"}
        )


class PromptInjectionGuardrail:
    """
    Detects prompt injection attacks and jailbreak attempts.
    """
    
    def __init__(self):
        # Common prompt injection patterns
        self.injection_patterns = [
            r'ignore (previous|all) instructions',
            r'disregard (previous|all) instructions',
            r'system prompt',
            r'you are now',
            r'forget (everything|all)',
            r'new instructions',
            r'override',
            r'sudo mode',
            r'developer mode',
            r'jailbreak'
        ]
        
        logger.info("prompt_injection_guardrail_initialized")
    
    def check(self, text: str) -> GuardrailResult:
        """
        Check for prompt injection attempts.
        
        Args:
            text: Input text to check
            
        Returns:
            GuardrailResult
        """
        violations = []
        text_lower = text.lower()
        
        for pattern in self.injection_patterns:
            if re.search(pattern, text_lower):
                violations.append({
                    "type": "prompt_injection",
                    "pattern": pattern,
                    "risk": "high"
                })
        
        passed = len(violations) == 0
        
        # Track metrics
        metrics.track_guardrail(
            check_type="prompt_injection",
            result="pass" if passed else "fail",
            violation=not passed,
            severity="critical" if violations else "low"
        )
        
        return GuardrailResult(
            passed=passed,
            violations=violations,
            metadata={"check_type": "prompt_injection"}
        )


class ContentLengthGuardrail:
    """Enforces input/output length limits."""
    
    def __init__(self, max_input_length: int = 5000, max_output_length: int = 2000):
        self.max_input_length = max_input_length
        self.max_output_length = max_output_length
    
    def check_input(self, text: str) -> GuardrailResult:
        """Check input length."""
        length = len(text)
        passed = length <= self.max_input_length
        
        violations = []
        if not passed:
            violations.append({
                "type": "input_length_exceeded",
                "length": length,
                "max": self.max_input_length
            })
        
        return GuardrailResult(passed=passed, violations=violations)
    
    def check_output(self, text: str) -> GuardrailResult:
        """Check output length."""
        length = len(text)
        passed = length <= self.max_output_length
        
        violations = []
        if not passed:
            violations.append({
                "type": "output_length_exceeded",
                "length": length,
                "max": self.max_output_length
            })
        
        return GuardrailResult(passed=passed, violations=violations)


class GuardrailsEngine:
    """
    Orchestrates all guardrails for comprehensive safety checking.
    """
    
    def __init__(self):
        self.pii_guardrail = PIIGuardrail() if (settings.pii_detection_enabled and PRESIDIO_AVAILABLE) else None
        self.toxicity_guardrail = ToxicityGuardrail(threshold=settings.toxicity_threshold)
        self.injection_guardrail = PromptInjectionGuardrail()
        self.length_guardrail = ContentLengthGuardrail()
        
        logger.info(
            "guardrails_engine_initialized",
            pii_enabled=self.pii_guardrail is not None,
            guardrails_enabled=settings.guardrails_enabled
        )
    
    def check_input(self, text: str) -> Dict[str, GuardrailResult]:
        """
        Run all input guardrails.
        
        Args:
            text: User input to check
            
        Returns:
            Dictionary of guardrail results
        """
        if not settings.guardrails_enabled:
            return {}
        
        results = {}
        
        # Check input length
        results["length"] = self.length_guardrail.check_input(text)
        
        # Check for PII
        if self.pii_guardrail:
            results["pii"] = self.pii_guardrail.check(text)
        
        # Check for toxicity
        results["toxicity"] = self.toxicity_guardrail.check(text)
        
        # Check for prompt injection
        results["injection"] = self.injection_guardrail.check(text)
        
        # Log aggregate results
        all_passed = all(r.passed for r in results.values())
        logger.info(
            "input_guardrails_completed",
            all_passed=all_passed,
            checks=list(results.keys())
        )
        
        return results
    
    def check_output(self, text: str) -> Dict[str, GuardrailResult]:
        """
        Run output guardrails.
        
        Args:
            text: AI output to check
            
        Returns:
            Dictionary of guardrail results
        """
        if not settings.guardrails_enabled:
            return {}
        
        results = {}
        
        # Check output length
        results["length"] = self.length_guardrail.check_output(text)
        
        # Check for PII in output
        if self.pii_guardrail:
            results["pii"] = self.pii_guardrail.check(text)
        
        # Check for toxicity in output
        results["toxicity"] = self.toxicity_guardrail.check(text)
        
        all_passed = all(r.passed for r in results.values())
        logger.info(
            "output_guardrails_completed",
            all_passed=all_passed,
            checks=list(results.keys())
        )
        
        return results
    
    def sanitize_text(self, text: str, guardrail_results: Dict[str, GuardrailResult]) -> str:
        """
        Sanitize text based on guardrail results.
        
        Args:
            text: Original text
            guardrail_results: Results from check_input/check_output
            
        Returns:
            Sanitized text
        """
        sanitized = text
        
        # Apply PII sanitization if available
        if "pii" in guardrail_results and guardrail_results["pii"].sanitized_text:
            sanitized = guardrail_results["pii"].sanitized_text
        
        return sanitized


# Global guardrails engine
guardrails_engine = GuardrailsEngine()


# Example usage
"""
from src.guardrails.engine import guardrails_engine

# Check user input
user_input = "My email is john@example.com and my phone is 555-1234"
input_results = guardrails_engine.check_input(user_input)

if not all(r.passed for r in input_results.values()):
    # Handle violations
    sanitized = guardrails_engine.sanitize_text(user_input, input_results)
    print(f"Sanitized: {sanitized}")

# Check AI output
ai_output = "Sure, I can help you with that harmful request..."
output_results = guardrails_engine.check_output(ai_output)

if not output_results["toxicity"].passed:
    # Reject toxic output
    raise ValueError("Generated toxic content")
"""
