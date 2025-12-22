"""
Synthetic Persona Testing for Childcare Customer Support Agent
Runs comprehensive tests with different customer personas and captures all metrics.

Output: JSON report with input, output, timing for each test
"""
import requests
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from enum import Enum


class CustomerPersona(Enum):
    """Different customer personas for testing"""
    NEW_PARENT = "new_parent"
    EXISTING_PARENT = "existing_parent"
    CONFUSED_CUSTOMER = "confused_customer"
    URGENT_INQUIRY = "urgent_inquiry"
    DETAILED_INQUIRY = "detailed_inquiry"
    BILLING_QUESTION = "billing_question"
    GENERAL_INFO = "general_info"


@dataclass
class TestCase:
    """A single test case"""
    persona: str
    question: str
    expected_topics: List[str]  # Expected keywords in response


@dataclass
class TestResult:
    """Result of a single test"""
    test_id: int
    persona: str
    input_question: str
    output_response: str
    response_length: int
    rag_enabled: bool
    rag_results_count: int
    total_time_ms: float
    llm_time_ms: float
    rag_time_ms: float
    success: bool
    error: str = None
    timestamp: str = None


# Childcare Center Customer Support Test Cases
TEST_CASES = [
    # New Parent Persona - First time inquiries
    TestCase(
        persona=CustomerPersona.NEW_PARENT.value,
        question="Hi, I'm interested in enrolling my child. What are the admission requirements?",
        expected_topics=["enrollment", "admission", "requirements"]
    ),
    TestCase(
        persona=CustomerPersona.NEW_PARENT.value,
        question="What age groups do you accept for enrollment?",
        expected_topics=["age", "group", "accept"]
    ),
    TestCase(
        persona=CustomerPersona.NEW_PARENT.value,
        question="What documents do I need to bring for registration?",
        expected_topics=["document", "registration", "bring"]
    ),
    
    # Billing/Payment Persona
    TestCase(
        persona=CustomerPersona.BILLING_QUESTION.value,
        question="What are the fees for the daycare program?",
        expected_topics=["fees", "payment", "cost"]
    ),
    TestCase(
        persona=CustomerPersona.BILLING_QUESTION.value,
        question="What payment methods do you accept?",
        expected_topics=["payment", "method", "accept"]
    ),
    TestCase(
        persona=CustomerPersona.BILLING_QUESTION.value,
        question="Is there a discount for siblings?",
        expected_topics=["discount", "sibling"]
    ),
    
    # Existing Parent Persona
    TestCase(
        persona=CustomerPersona.EXISTING_PARENT.value,
        question="What are your operating hours?",
        expected_topics=["hours", "time", "open"]
    ),
    TestCase(
        persona=CustomerPersona.EXISTING_PARENT.value,
        question="What is the pickup policy?",
        expected_topics=["pickup", "policy"]
    ),
    TestCase(
        persona=CustomerPersona.EXISTING_PARENT.value,
        question="How do I update my emergency contact information?",
        expected_topics=["emergency", "contact", "update"]
    ),
    
    # Urgent Inquiry Persona
    TestCase(
        persona=CustomerPersona.URGENT_INQUIRY.value,
        question="My child is sick, what is your illness policy?",
        expected_topics=["sick", "illness", "policy", "health"]
    ),
    TestCase(
        persona=CustomerPersona.URGENT_INQUIRY.value,
        question="I need to pick up my child early today, what's the process?",
        expected_topics=["pickup", "early", "process"]
    ),
    
    # Detailed Inquiry Persona
    TestCase(
        persona=CustomerPersona.DETAILED_INQUIRY.value,
        question="Can you explain your curriculum and daily activities?",
        expected_topics=["curriculum", "activities", "daily"]
    ),
    TestCase(
        persona=CustomerPersona.DETAILED_INQUIRY.value,
        question="What safety measures do you have in place?",
        expected_topics=["safety", "security", "measure"]
    ),
    TestCase(
        persona=CustomerPersona.DETAILED_INQUIRY.value,
        question="Tell me about the staff qualifications and training",
        expected_topics=["staff", "qualification", "training"]
    ),
    
    # General Info Persona
    TestCase(
        persona=CustomerPersona.GENERAL_INFO.value,
        question="What meals and snacks do you provide?",
        expected_topics=["meal", "snack", "food"]
    ),
    TestCase(
        persona=CustomerPersona.GENERAL_INFO.value,
        question="Do you provide transportation services?",
        expected_topics=["transport", "service"]
    ),
    
    # Confused Customer Persona
    TestCase(
        persona=CustomerPersona.CONFUSED_CUSTOMER.value,
        question="I'm not sure what I need to do to get started",
        expected_topics=["start", "help", "step"]
    ),
    TestCase(
        persona=CustomerPersona.CONFUSED_CUSTOMER.value,
        question="Can you help me understand the enrollment process?",
        expected_topics=["enroll", "process", "help"]
    ),
]


class SyntheticTestRunner:
    """Run synthetic tests against the Customer Support Agent"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:9011"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def run_single_test(self, test_id: int, test_case: TestCase) -> TestResult:
        """Run a single test case and capture all metrics"""
        print(f"\n[Test {test_id}] Persona: {test_case.persona}")
        print(f"  Question: {test_case.question[:60]}...")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/conversation",
                json={
                    "message": test_case.question,
                    "conversation_id": f"synthetic_test_{test_id}_{int(time.time())}"
                },
                timeout=120  # 2 minute timeout for slow models
            )
            
            total_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                result = TestResult(
                    test_id=test_id,
                    persona=test_case.persona,
                    input_question=test_case.question,
                    output_response=data.get("response", ""),
                    response_length=len(data.get("response", "")),
                    rag_enabled=data.get("metadata", {}).get("rag_enabled", False),
                    rag_results_count=data.get("metadata", {}).get("rag_results_count", 0),
                    total_time_ms=data.get("timing", {}).get("total_ms", total_time),
                    llm_time_ms=data.get("timing", {}).get("llm_ms", 0),
                    rag_time_ms=data.get("timing", {}).get("rag_ms", 0),
                    success=True,
                    timestamp=datetime.now().isoformat()
                )
                
                print(f"  ✅ Success | Time: {result.total_time_ms:.0f}ms | RAG: {result.rag_results_count} docs")
                print(f"  Response: {result.output_response[:100]}...")
                
            else:
                result = TestResult(
                    test_id=test_id,
                    persona=test_case.persona,
                    input_question=test_case.question,
                    output_response="",
                    response_length=0,
                    rag_enabled=False,
                    rag_results_count=0,
                    total_time_ms=total_time,
                    llm_time_ms=0,
                    rag_time_ms=0,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                    timestamp=datetime.now().isoformat()
                )
                print(f"  ❌ Failed: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            result = TestResult(
                test_id=test_id,
                persona=test_case.persona,
                input_question=test_case.question,
                output_response="",
                response_length=0,
                rag_enabled=False,
                rag_results_count=0,
                total_time_ms=(time.time() - start_time) * 1000,
                llm_time_ms=0,
                rag_time_ms=0,
                success=False,
                error="Request timeout (>120s)",
                timestamp=datetime.now().isoformat()
            )
            print(f"  ❌ Timeout")
            
        except Exception as e:
            result = TestResult(
                test_id=test_id,
                persona=test_case.persona,
                input_question=test_case.question,
                output_response="",
                response_length=0,
                rag_enabled=False,
                rag_results_count=0,
                total_time_ms=(time.time() - start_time) * 1000,
                llm_time_ms=0,
                rag_time_ms=0,
                success=False,
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
            print(f"  ❌ Error: {e}")
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and generate report"""
        print("=" * 70)
        print("🧪 SYNTHETIC PERSONA TESTS - Childcare Customer Support Agent")
        print("=" * 70)
        print(f"Total Tests: {len(TEST_CASES)}")
        print(f"Start Time: {datetime.now().isoformat()}")
        
        self.start_time = time.time()
        self.results = []
        
        for i, test_case in enumerate(TEST_CASES, 1):
            result = self.run_single_test(i, test_case)
            self.results.append(result)
        
        self.end_time = time.time()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        # Calculate timing statistics
        if successful:
            times = [r.total_time_ms for r in successful]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            llm_times = [r.llm_time_ms for r in successful if r.llm_time_ms > 0]
            avg_llm_time = sum(llm_times) / len(llm_times) if llm_times else 0
            
            rag_times = [r.rag_time_ms for r in successful if r.rag_time_ms > 0]
            avg_rag_time = sum(rag_times) / len(rag_times) if rag_times else 0
        else:
            avg_time = min_time = max_time = avg_llm_time = avg_rag_time = 0
        
        # Group by persona
        persona_stats = {}
        for result in self.results:
            if result.persona not in persona_stats:
                persona_stats[result.persona] = {"success": 0, "failed": 0, "total_time": 0}
            
            if result.success:
                persona_stats[result.persona]["success"] += 1
                persona_stats[result.persona]["total_time"] += result.total_time_ms
            else:
                persona_stats[result.persona]["failed"] += 1
        
        # Calculate average per persona
        for persona, stats in persona_stats.items():
            if stats["success"] > 0:
                stats["avg_time_ms"] = stats["total_time"] / stats["success"]
            else:
                stats["avg_time_ms"] = 0
        
        report = {
            "test_run": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
                "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
                "total_duration_seconds": round(self.end_time - self.start_time, 2) if self.end_time and self.start_time else 0
            },
            "summary": {
                "total_tests": len(self.results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": f"{(len(successful) / len(self.results) * 100):.1f}%" if self.results else "0%"
            },
            "timing_stats": {
                "average_response_ms": round(avg_time, 2),
                "min_response_ms": round(min_time, 2),
                "max_response_ms": round(max_time, 2),
                "average_llm_ms": round(avg_llm_time, 2),
                "average_rag_ms": round(avg_rag_time, 2)
            },
            "persona_breakdown": persona_stats,
            "rag_stats": {
                "tests_with_rag": len([r for r in successful if r.rag_enabled]),
                "avg_rag_docs_retrieved": round(
                    sum(r.rag_results_count for r in successful) / len(successful), 1
                ) if successful else 0
            },
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "data/eval_datasets"):
        """Save report to JSON file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"synthetic_test_report_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report saved to: {filepath}")
        return filepath
    
    def print_summary(self, report: Dict[str, Any]):
        """Print formatted summary to console"""
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        summary = report["summary"]
        timing = report["timing_stats"]
        
        print(f"\n✅ Successful: {summary['successful']}/{summary['total_tests']} ({summary['success_rate']})")
        print(f"❌ Failed: {summary['failed']}")
        
        print(f"\n⏱️  TIMING STATISTICS:")
        print(f"   Average Response Time: {timing['average_response_ms']:.0f}ms")
        print(f"   Min Response Time: {timing['min_response_ms']:.0f}ms")
        print(f"   Max Response Time: {timing['max_response_ms']:.0f}ms")
        print(f"   Average LLM Time: {timing['average_llm_ms']:.0f}ms")
        print(f"   Average RAG Time: {timing['average_rag_ms']:.0f}ms")
        
        print(f"\n📚 RAG STATISTICS:")
        rag_stats = report["rag_stats"]
        print(f"   Tests with RAG: {rag_stats['tests_with_rag']}")
        print(f"   Avg Docs Retrieved: {rag_stats['avg_rag_docs_retrieved']}")
        
        print(f"\n👥 PERSONA BREAKDOWN:")
        for persona, stats in report["persona_breakdown"].items():
            status = "✅" if stats["failed"] == 0 else "⚠️"
            print(f"   {status} {persona}: {stats['success']}/{stats['success'] + stats['failed']} | Avg: {stats['avg_time_ms']:.0f}ms")
        
        print("\n" + "=" * 70)


def main():
    """Main entry point"""
    runner = SyntheticTestRunner()
    
    # Check if server is running
    try:
        health = requests.get(f"{runner.base_url}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Server is not healthy. Please start the server first.")
            return
    except:
        print("❌ Cannot connect to server at", runner.base_url)
        print("   Please start the server: python -m uvicorn src.api.main:app --port 9011")
        return
    
    # Run tests
    report = runner.run_all_tests()
    
    # Print summary
    runner.print_summary(report)
    
    # Save report
    filepath = runner.save_report(report)
    
    print(f"\n🎉 Testing Complete!")
    print(f"   Full report: {filepath}")


if __name__ == "__main__":
    main()
