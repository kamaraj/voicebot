"""
Synthetic Persona Testing - ROUND 2: Rephrased Questions
Different tones, words, and sentence structures for the same topics.
"""
import requests
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from enum import Enum


class CustomerTone(Enum):
    """Different customer communication tones"""
    CASUAL = "casual"
    FORMAL = "formal"
    FRUSTRATED = "frustrated"
    POLITE = "polite"
    DIRECT = "direct"
    CONFUSED = "confused"
    URGENT = "urgent"


@dataclass
class TestCase:
    persona: str
    question: str
    original_topic: str


@dataclass
class TestResult:
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


# REPHRASED TEST CASES - Same topics, different phrasing
REPHRASED_TEST_CASES = [
    # Admission/Enrollment - Different phrasings
    TestCase(
        persona=CustomerTone.CASUAL.value,
        question="Hey, so like what do I gotta do to sign my kid up here?",
        original_topic="admission_requirements"
    ),
    TestCase(
        persona=CustomerTone.FORMAL.value,
        question="Good afternoon. I would like to inquire about the prerequisites for enrolling my child at your institution.",
        original_topic="admission_requirements"
    ),
    TestCase(
        persona=CustomerTone.DIRECT.value,
        question="Enrollment steps. What are they?",
        original_topic="admission_requirements"
    ),
    
    # Age Requirements - Different phrasings
    TestCase(
        persona=CustomerTone.POLITE.value,
        question="Could you kindly tell me the age range for children you admit?",
        original_topic="age_groups"
    ),
    TestCase(
        persona=CustomerTone.CASUAL.value,
        question="My toddler is 2 years old, is that cool for joining?",
        original_topic="age_groups"
    ),
    
    # Documents/Registration - Different phrasings
    TestCase(
        persona=CustomerTone.CONFUSED.value,
        question="I'm a bit lost on what paperwork I should bring when I come in?",
        original_topic="documents_needed"
    ),
    TestCase(
        persona=CustomerTone.DIRECT.value,
        question="List of documents for registration please.",
        original_topic="documents_needed"
    ),
    
    # Fees/Payment - Different phrasings
    TestCase(
        persona=CustomerTone.FRUSTRATED.value,
        question="Nobody has told me clearly - how much does this daycare actually cost?",
        original_topic="fees"
    ),
    TestCase(
        persona=CustomerTone.POLITE.value,
        question="Would you be so kind as to provide the fee structure for your programs?",
        original_topic="fees"
    ),
    TestCase(
        persona=CustomerTone.CASUAL.value,
        question="What's the damage gonna be per month for childcare?",
        original_topic="fees"
    ),
    
    # Payment Methods - Different phrasings
    TestCase(
        persona=CustomerTone.DIRECT.value,
        question="Do you take credit cards or only cash?",
        original_topic="payment_methods"
    ),
    TestCase(
        persona=CustomerTone.FORMAL.value,
        question="I wish to understand the various modes of payment that your establishment accepts.",
        original_topic="payment_methods"
    ),
    
    # Operating Hours - Different phrasings
    TestCase(
        persona=CustomerTone.URGENT.value,
        question="Quick question - when do you open and close? I work early shifts.",
        original_topic="operating_hours"
    ),
    TestCase(
        persona=CustomerTone.CASUAL.value,
        question="What time do you guys open up in the morning?",
        original_topic="operating_hours"
    ),
    
    # Pickup Policy - Different phrasings
    TestCase(
        persona=CustomerTone.CONFUSED.value,
        question="If my husband wants to pick up our daughter, does he need anything special?",
        original_topic="pickup_policy"
    ),
    TestCase(
        persona=CustomerTone.DIRECT.value,
        question="Rules for picking up kids - what should I know?",
        original_topic="pickup_policy"
    ),
    
    # Illness Policy - Different phrasings
    TestCase(
        persona=CustomerTone.URGENT.value,
        question="My kid woke up with a fever this morning! What's your sick child policy?",
        original_topic="illness_policy"
    ),
    TestCase(
        persona=CustomerTone.POLITE.value,
        question="May I ask what happens if a child becomes unwell during the day?",
        original_topic="illness_policy"
    ),
    
    # Curriculum - Different phrasings
    TestCase(
        persona=CustomerTone.FORMAL.value,
        question="Could you elaborate on the educational curriculum and developmental activities offered?",
        original_topic="curriculum"
    ),
    TestCase(
        persona=CustomerTone.CASUAL.value,
        question="What kind of stuff do the kids do all day? Is it just playing or learning too?",
        original_topic="curriculum"
    ),
    
    # Safety - Different phrasings
    TestCase(
        persona=CustomerTone.CONCERNED.value if hasattr(CustomerTone, 'CONCERNED') else CustomerTone.POLITE.value,
        question="As a first-time parent, I'm worried about safety. What precautions do you take?",
        original_topic="safety_measures"
    ),
    TestCase(
        persona=CustomerTone.DIRECT.value,
        question="Security cameras? Background checks? What's your safety setup?",
        original_topic="safety_measures"
    ),
    
    # Meals - Different phrasings
    TestCase(
        persona=CustomerTone.CASUAL.value,
        question="Do the kids get fed here or do I pack lunch?",
        original_topic="meals"
    ),
    TestCase(
        persona=CustomerTone.POLITE.value,
        question="I was wondering about the meal arrangements - are meals included in the program?",
        original_topic="meals"
    ),
    
    # Getting Started - Different phrasings
    TestCase(
        persona=CustomerTone.CONFUSED.value,
        question="This is overwhelming. Where do I even begin with all of this?",
        original_topic="getting_started"
    ),
    TestCase(
        persona=CustomerTone.FRUSTRATED.value,
        question="I've been trying to figure out how to enroll for an hour. Can you just walk me through it simply?",
        original_topic="getting_started"
    ),
]


class SyntheticTestRunner:
    def __init__(self, base_url: str = "http://127.0.0.1:9011"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def run_single_test(self, test_id: int, test_case: TestCase) -> TestResult:
        print(f"\n[Test {test_id}] Tone: {test_case.persona} | Topic: {test_case.original_topic}")
        print(f"  Q: {test_case.question[:70]}...")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/conversation",
                json={
                    "message": test_case.question,
                    "conversation_id": f"rephrased_test_{test_id}_{int(time.time())}"
                },
                timeout=120
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
                print(f"  A: {result.output_response[:100]}...")
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
                    error=f"HTTP {response.status_code}",
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
                error="Timeout",
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
        print("=" * 80)
        print("🧪 REPHRASED PERSONA TESTS - Round 2")
        print("    Different tones, words, and sentence structures")
        print("=" * 80)
        print(f"Total Tests: {len(REPHRASED_TEST_CASES)}")
        print(f"Start Time: {datetime.now().isoformat()}")
        
        self.start_time = time.time()
        self.results = []
        
        for i, test_case in enumerate(REPHRASED_TEST_CASES, 1):
            result = self.run_single_test(i, test_case)
            self.results.append(result)
        
        self.end_time = time.time()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
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
        
        # Group by tone
        tone_stats = {}
        for result in self.results:
            if result.persona not in tone_stats:
                tone_stats[result.persona] = {"success": 0, "failed": 0, "total_time": 0}
            
            if result.success:
                tone_stats[result.persona]["success"] += 1
                tone_stats[result.persona]["total_time"] += result.total_time_ms
            else:
                tone_stats[result.persona]["failed"] += 1
        
        for tone, stats in tone_stats.items():
            if stats["success"] > 0:
                stats["avg_time_ms"] = stats["total_time"] / stats["success"]
            else:
                stats["avg_time_ms"] = 0
        
        report = {
            "test_run": {
                "name": "Rephrased Questions - Round 2",
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
            "tone_breakdown": tone_stats,
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
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rephrased_test_report_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report saved to: {filepath}")
        return filepath
    
    def print_summary(self, report: Dict[str, Any]):
        print("\n" + "=" * 80)
        print("📊 REPHRASED TEST RESULTS SUMMARY")
        print("=" * 80)
        
        summary = report["summary"]
        timing = report["timing_stats"]
        
        print(f"\n✅ Successful: {summary['successful']}/{summary['total_tests']} ({summary['success_rate']})")
        print(f"❌ Failed: {summary['failed']}")
        
        print(f"\n⏱️  TIMING STATISTICS:")
        print(f"   Average Response Time: {timing['average_response_ms']:.0f}ms")
        print(f"   Min Response Time: {timing['min_response_ms']:.0f}ms")
        print(f"   Max Response Time: {timing['max_response_ms']:.0f}ms")
        
        print(f"\n🗣️  TONE BREAKDOWN:")
        for tone, stats in report["tone_breakdown"].items():
            status = "✅" if stats["failed"] == 0 else "⚠️"
            print(f"   {status} {tone}: {stats['success']}/{stats['success'] + stats['failed']} | Avg: {stats['avg_time_ms']:.0f}ms")
        
        print("\n" + "=" * 80)
        
        # Print table
        print("\n📋 DETAILED RESULTS TABLE")
        print("-" * 120)
        print(f"{'#':<3} | {'Tone':<12} | {'Question':<45} | {'Answer':<40} | {'Time':<8} | {'Docs':<4}")
        print("-" * 120)
        for r in report['detailed_results']:
            q = r['input_question'][:43] + ".." if len(r['input_question']) > 45 else r['input_question']
            a = r['output_response'][:38] + ".." if len(r['output_response']) > 40 else r['output_response']
            a = a.replace('\n', ' ')
            status = "PASS" if r['success'] else "FAIL"
            print(f"{r['test_id']:<3} | {r['persona']:<12} | {q:<45} | {a:<40} | {r['total_time_ms']:<8.0f} | {r['rag_results_count']:<4}")


def main():
    runner = SyntheticTestRunner()
    
    # Check if server is running
    try:
        health = requests.get(f"{runner.base_url}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Server is not healthy.")
            return
    except:
        print("❌ Cannot connect to server.")
        return
    
    # Run tests
    report = runner.run_all_tests()
    
    # Print summary
    runner.print_summary(report)
    
    # Save report
    filepath = runner.save_report(report)
    
    print(f"\n🎉 Testing Complete!")


if __name__ == "__main__":
    main()
