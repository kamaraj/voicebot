"""
Attendance Question Evaluation Script.
Tests the VoiceBot's ability to understand and respond to
different phrasings of attendance-related questions.

Usage:
    python scripts/eval_attendance_questions.py --api-url https://voicebot-kamaraj-v1.vercel.app
    python scripts/eval_attendance_questions.py --api-url http://localhost:9011
"""
import asyncio
import aiohttp
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


class QuestionTone(Enum):
    """Different tones for question variations."""
    DIRECT = "direct"
    CASUAL = "casual"
    FORMAL = "formal"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    ACTION = "action"
    PARENT = "parent"
    STAFF = "staff"
    CONTEXT = "context"
    TIME = "time"


@dataclass
class TestCase:
    """A single test case for evaluation."""
    question: str
    tone: QuestionTone
    topic: str
    expected_keywords: List[str]  # Keywords expected in response
    context: Optional[str] = None


@dataclass
class TestResult:
    """Result of a single test case."""
    test_case: Dict[str, Any]
    response: str
    success: bool
    keywords_found: List[str]
    keywords_missing: List[str]
    response_time_ms: float
    error: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass 
class EvalSummary:
    """Summary of an evaluation run."""
    eval_id: str
    timestamp: str
    api_url: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    by_tone: Dict[str, Dict[str, Any]]
    results: List[Dict]


# ============================================================================
# ATTENDANCE TEST CASES
# ============================================================================

ATTENDANCE_TEST_CASES = [
    # Direct Questions
    TestCase(
        question="How do I mark daily attendance?",
        tone=QuestionTone.DIRECT,
        topic="attendance",
        expected_keywords=["attendance", "mark", "record", "check", "sign"]
    ),
    TestCase(
        question="How can I record attendance for today?",
        tone=QuestionTone.DIRECT,
        topic="attendance",
        expected_keywords=["attendance", "record", "today"]
    ),
    TestCase(
        question="What's the process for marking attendance?",
        tone=QuestionTone.DIRECT,
        topic="attendance",
        expected_keywords=["attendance", "process", "mark"]
    ),
    TestCase(
        question="Where do I log student attendance?",
        tone=QuestionTone.DIRECT,
        topic="attendance",
        expected_keywords=["attendance", "log", "student"]
    ),
    TestCase(
        question="How do I take attendance in the system?",
        tone=QuestionTone.DIRECT,
        topic="attendance",
        expected_keywords=["attendance", "system"]
    ),
    
    # Casual/Informal Tone
    TestCase(
        question="Hey, how do I mark kids as present today?",
        tone=QuestionTone.CASUAL,
        topic="attendance",
        expected_keywords=["attendance", "mark", "present"]
    ),
    TestCase(
        question="Quick question - where do I check in students?",
        tone=QuestionTone.CASUAL,
        topic="attendance",
        expected_keywords=["check", "student"]
    ),
    TestCase(
        question="How do I show that my child came to school today?",
        tone=QuestionTone.CASUAL,
        topic="attendance",
        expected_keywords=["attendance", "child"]
    ),
    TestCase(
        question="So, what's the deal with attendance marking?",
        tone=QuestionTone.CASUAL,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    TestCase(
        question="Can you tell me how to do the attendance thing?",
        tone=QuestionTone.CASUAL,
        topic="attendance",
        expected_keywords=["attendance"]
    ),
    
    # Formal/Professional Tone
    TestCase(
        question="Could you please explain the procedure for recording daily attendance?",
        tone=QuestionTone.FORMAL,
        topic="attendance",
        expected_keywords=["attendance", "procedure", "record"]
    ),
    TestCase(
        question="I would like to understand how to document student attendance properly.",
        tone=QuestionTone.FORMAL,
        topic="attendance",
        expected_keywords=["attendance", "document", "student"]
    ),
    TestCase(
        question="What is the standard process for registering a child's attendance?",
        tone=QuestionTone.FORMAL,
        topic="attendance",
        expected_keywords=["attendance", "process", "child"]
    ),
    TestCase(
        question="Please provide instructions for the daily attendance marking system.",
        tone=QuestionTone.FORMAL,
        topic="attendance",
        expected_keywords=["attendance", "instructions"]
    ),
    TestCase(
        question="Kindly guide me through the attendance registration process.",
        tone=QuestionTone.FORMAL,
        topic="attendance",
        expected_keywords=["attendance", "registration", "guide"]
    ),
    
    # Action-Oriented/Commands
    TestCase(
        question="Show me how to mark attendance",
        tone=QuestionTone.ACTION,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    TestCase(
        question="Help me record today's attendance",
        tone=QuestionTone.ACTION,
        topic="attendance",
        expected_keywords=["attendance", "record"]
    ),
    TestCase(
        question="Guide me through the attendance process",
        tone=QuestionTone.ACTION,
        topic="attendance",
        expected_keywords=["attendance", "process"]
    ),
    TestCase(
        question="Walk me through checking in students",
        tone=QuestionTone.ACTION,
        topic="attendance",
        expected_keywords=["check", "student"]
    ),
    TestCase(
        question="Tell me the steps to log attendance",
        tone=QuestionTone.ACTION,
        topic="attendance",
        expected_keywords=["attendance", "steps", "log"]
    ),
    
    # Confused/Uncertain Tone
    TestCase(
        question="I'm not sure how to mark attendance... can you help?",
        tone=QuestionTone.CONFUSED,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    TestCase(
        question="I'm confused about the attendance system, how does it work?",
        tone=QuestionTone.CONFUSED,
        topic="attendance",
        expected_keywords=["attendance", "system"]
    ),
    TestCase(
        question="Is there a way to mark attendance? I can't figure it out.",
        tone=QuestionTone.CONFUSED,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    TestCase(
        question="I don't understand - how do I show my child was present?",
        tone=QuestionTone.CONFUSED,
        topic="attendance",
        expected_keywords=["attendance", "present", "child"]
    ),
    TestCase(
        question="What am I supposed to do for attendance each day?",
        tone=QuestionTone.CONFUSED,
        topic="attendance",
        expected_keywords=["attendance", "day"]
    ),
    
    # Frustrated Tone
    TestCase(
        question="Why is it so hard to mark attendance? Just tell me how!",
        tone=QuestionTone.FRUSTRATED,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    TestCase(
        question="I've been trying to figure out the attendance thing - help!",
        tone=QuestionTone.FRUSTRATED,
        topic="attendance",
        expected_keywords=["attendance"]
    ),
    TestCase(
        question="The attendance system is confusing - how does it work?",
        tone=QuestionTone.FRUSTRATED,
        topic="attendance",
        expected_keywords=["attendance", "system"]
    ),
    TestCase(
        question="I can't find where to mark attendance anywhere!",
        tone=QuestionTone.FRUSTRATED,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    TestCase(
        question="How am I supposed to mark attendance if there's no clear option?",
        tone=QuestionTone.FRUSTRATED,
        topic="attendance",
        expected_keywords=["attendance", "mark"]
    ),
    
    # Parent Perspective
    TestCase(
        question="How do I let the center know my child will be there today?",
        tone=QuestionTone.PARENT,
        topic="attendance",
        expected_keywords=["child", "attendance"]
    ),
    TestCase(
        question="What should I do to confirm my kid's attendance?",
        tone=QuestionTone.PARENT,
        topic="attendance",
        expected_keywords=["attendance", "confirm"]
    ),
    TestCase(
        question="How do parents mark their children as attending?",
        tone=QuestionTone.PARENT,
        topic="attendance",
        expected_keywords=["parent", "children", "attending"]
    ),
    TestCase(
        question="Do I need to sign in my child every day?",
        tone=QuestionTone.PARENT,
        topic="attendance",
        expected_keywords=["sign", "child", "day"]
    ),
    TestCase(
        question="What's the check-in process when I drop off my child?",
        tone=QuestionTone.PARENT,
        topic="attendance",
        expected_keywords=["check", "drop", "child"]
    ),
    
    # Staff/Teacher Perspective
    TestCase(
        question="How do teachers record class attendance?",
        tone=QuestionTone.STAFF,
        topic="attendance",
        expected_keywords=["teacher", "attendance", "class"]
    ),
    TestCase(
        question="What's the process for staff to mark attendance in the morning?",
        tone=QuestionTone.STAFF,
        topic="attendance",
        expected_keywords=["staff", "attendance", "morning"]
    ),
    TestCase(
        question="How do I check students in when they arrive?",
        tone=QuestionTone.STAFF,
        topic="attendance",
        expected_keywords=["check", "student", "arrive"]
    ),
    TestCase(
        question="As a teacher, how do I log who's present in my class?",
        tone=QuestionTone.STAFF,
        topic="attendance",
        expected_keywords=["teacher", "present", "class"]
    ),
    TestCase(
        question="What's the attendance procedure for childcare workers?",
        tone=QuestionTone.STAFF,
        topic="attendance",
        expected_keywords=["attendance", "childcare"]
    ),
    
    # Specific Context Questions
    TestCase(
        question="How do I mark attendance if my child arrives late?",
        tone=QuestionTone.CONTEXT,
        topic="late_arrival",
        expected_keywords=["attendance", "late", "arrive"]
    ),
    TestCase(
        question="Can I mark attendance in advance for tomorrow?",
        tone=QuestionTone.CONTEXT,
        topic="advance_marking",
        expected_keywords=["attendance", "advance", "tomorrow"]
    ),
    TestCase(
        question="What if I forgot to mark attendance yesterday?",
        tone=QuestionTone.CONTEXT,
        topic="missed_attendance",
        expected_keywords=["attendance", "forgot"]
    ),
    TestCase(
        question="How do I change an attendance record if I made a mistake?",
        tone=QuestionTone.CONTEXT,
        topic="edit_attendance",
        expected_keywords=["attendance", "change", "mistake"]
    ),
    TestCase(
        question="Is there a mobile app to mark attendance?",
        tone=QuestionTone.CONTEXT,
        topic="mobile_app",
        expected_keywords=["app", "attendance"]
    ),
    
    # Time-Related Variations
    TestCase(
        question="What time should I mark attendance?",
        tone=QuestionTone.TIME,
        topic="attendance_time",
        expected_keywords=["time", "attendance"]
    ),
    TestCase(
        question="How early can I check in my child?",
        tone=QuestionTone.TIME,
        topic="early_checkin",
        expected_keywords=["check", "early", "child"]
    ),
    TestCase(
        question="Is there a deadline for marking daily attendance?",
        tone=QuestionTone.TIME,
        topic="attendance_deadline",
        expected_keywords=["deadline", "attendance"]
    ),
    TestCase(
        question="Can I mark attendance after school hours?",
        tone=QuestionTone.TIME,
        topic="after_hours",
        expected_keywords=["attendance", "hours"]
    ),
    TestCase(
        question="What happens if I miss the attendance window?",
        tone=QuestionTone.TIME,
        topic="missed_window",
        expected_keywords=["attendance", "miss"]
    ),
]


class AttendanceEvaluator:
    """Evaluator for attendance-related questions."""
    
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/")
        self.conversation_endpoint = f"{self.api_url}/conversation"
        
    async def send_message(self, message: str, session: aiohttp.ClientSession) -> Dict:
        """Send a message to the API and get response."""
        payload = {
            "message": message,
            "conversation_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(message) % 10000}"
        }
        
        start_time = time.time()
        
        try:
            async with session.post(
                self.conversation_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "metadata": data.get("metadata", {}),
                        "timing": data.get("timing", {}),
                        "response_time_ms": elapsed_ms
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "response_time_ms": elapsed_ms
                    }
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": elapsed_ms
            }
    
    def check_keywords(self, response: str, expected_keywords: List[str]) -> tuple:
        """Check which expected keywords are present in response."""
        response_lower = response.lower()
        found = []
        missing = []
        
        for keyword in expected_keywords:
            if keyword.lower() in response_lower:
                found.append(keyword)
            else:
                missing.append(keyword)
        
        return found, missing
    
    async def evaluate_test_case(
        self, 
        test_case: TestCase, 
        session: aiohttp.ClientSession
    ) -> TestResult:
        """Evaluate a single test case."""
        result = await self.send_message(test_case.question, session)
        
        if result["success"]:
            found, missing = self.check_keywords(
                result["response"], 
                test_case.expected_keywords
            )
            
            # Success if at least 50% of keywords are found
            keyword_match_rate = len(found) / len(test_case.expected_keywords) if test_case.expected_keywords else 1.0
            success = keyword_match_rate >= 0.5 and len(result["response"]) > 20
            
            # Convert test_case to dict with tone as string
            test_case_dict = {
                "question": test_case.question,
                "tone": test_case.tone.value,
                "topic": test_case.topic,
                "expected_keywords": test_case.expected_keywords,
                "context": test_case.context
            }
            
            return TestResult(
                test_case=test_case_dict,
                response=result["response"],
                success=success,
                keywords_found=found,
                keywords_missing=missing,
                response_time_ms=result["response_time_ms"],
                metadata=result.get("metadata")
            )
        else:
            # Convert test_case to dict with tone as string
            test_case_dict = {
                "question": test_case.question,
                "tone": test_case.tone.value,
                "topic": test_case.topic,
                "expected_keywords": test_case.expected_keywords,
                "context": test_case.context
            }
            
            return TestResult(
                test_case=test_case_dict,
                response="",
                success=False,
                keywords_found=[],
                keywords_missing=test_case.expected_keywords,
                response_time_ms=result["response_time_ms"],
                error=result.get("error")
            )
    
    async def run_evaluation(
        self, 
        test_cases: List[TestCase],
        concurrency: int = 3
    ) -> EvalSummary:
        """Run evaluation on all test cases."""
        eval_id = f"attendance_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results: List[TestResult] = []
        
        print(f"\n{'='*60}")
        print(f"  ATTENDANCE QUESTION EVALUATION")
        print(f"  API: {self.api_url}")
        print(f"  Total Tests: {len(test_cases)}")
        print(f"{'='*60}\n")
        
        connector = aiohttp.TCPConnector(limit=concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Run tests with limited concurrency
            semaphore = asyncio.Semaphore(concurrency)
            
            async def run_with_semaphore(tc: TestCase, idx: int) -> TestResult:
                async with semaphore:
                    result = await self.evaluate_test_case(tc, session)
                    status = "✅" if result.success else "❌"
                    print(f"{status} [{idx+1}/{len(test_cases)}] [{tc.tone.value}] {tc.question[:50]}...")
                    return result
            
            tasks = [
                run_with_semaphore(tc, idx) 
                for idx, tc in enumerate(test_cases)
            ]
            results = await asyncio.gather(*tasks)
        
        # Calculate statistics
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        response_times = [r.response_time_ms for r in results]
        
        # Group by tone
        by_tone = {}
        for tone in QuestionTone:
            tone_results = [r for r in results if r.test_case["tone"] == tone.value]
            if tone_results:
                tone_passed = sum(1 for r in tone_results if r.success)
                tone_times = [r.response_time_ms for r in tone_results]
                by_tone[tone.value] = {
                    "total": len(tone_results),
                    "passed": tone_passed,
                    "failed": len(tone_results) - tone_passed,
                    "pass_rate": tone_passed / len(tone_results) * 100,
                    "avg_response_time_ms": statistics.mean(tone_times)
                }
        
        summary = EvalSummary(
            eval_id=eval_id,
            timestamp=datetime.now().isoformat(),
            api_url=self.api_url,
            total_tests=len(test_cases),
            passed=passed,
            failed=failed,
            pass_rate=passed / len(test_cases) * 100,
            avg_response_time_ms=statistics.mean(response_times),
            min_response_time_ms=min(response_times),
            max_response_time_ms=max(response_times),
            p95_response_time_ms=sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0],
            by_tone=by_tone,
            results=[asdict(r) for r in results]
        )
        
        return summary
    
    def print_summary(self, summary: EvalSummary):
        """Print evaluation summary."""
        print(f"\n{'='*60}")
        print(f"  EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"  Eval ID: {summary.eval_id}")
        print(f"  Timestamp: {summary.timestamp}")
        print(f"  API URL: {summary.api_url}")
        print(f"{'='*60}")
        
        print(f"\n📊 OVERALL RESULTS")
        print(f"  ├─ Total Tests: {summary.total_tests}")
        print(f"  ├─ Passed: {summary.passed} ✅")
        print(f"  ├─ Failed: {summary.failed} ❌")
        print(f"  └─ Pass Rate: {summary.pass_rate:.1f}%")
        
        print(f"\n⏱️  RESPONSE TIME STATS")
        print(f"  ├─ Average: {summary.avg_response_time_ms:.0f}ms")
        print(f"  ├─ Min: {summary.min_response_time_ms:.0f}ms")
        print(f"  ├─ Max: {summary.max_response_time_ms:.0f}ms")
        print(f"  └─ P95: {summary.p95_response_time_ms:.0f}ms")
        
        print(f"\n📋 RESULTS BY TONE")
        for tone, stats in summary.by_tone.items():
            status = "✅" if stats["pass_rate"] >= 80 else "⚠️" if stats["pass_rate"] >= 50 else "❌"
            print(f"  {status} {tone.upper()}")
            print(f"     ├─ Pass Rate: {stats['pass_rate']:.1f}% ({stats['passed']}/{stats['total']})")
            print(f"     └─ Avg Time: {stats['avg_response_time_ms']:.0f}ms")
        
        # Show failed cases
        failed_results = [r for r in summary.results if not r["success"]]
        if failed_results:
            print(f"\n❌ FAILED TESTS ({len(failed_results)})")
            for r in failed_results[:5]:  # Show first 5
                print(f"  ├─ Question: {r['test_case']['question'][:60]}...")
                if r.get("error"):
                    print(f"  │  Error: {r['error'][:80]}")
                else:
                    print(f"  │  Missing Keywords: {r['keywords_missing']}")
            if len(failed_results) > 5:
                print(f"  └─ ... and {len(failed_results) - 5} more")
        
        print(f"\n{'='*60}")
    
    def save_results(self, summary: EvalSummary, output_dir: str = "data/eval_datasets"):
        """Save evaluation results to JSON file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{summary.eval_id}.json"
        filepath = output_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filepath}")
        
        # Also create a markdown report
        self.save_markdown_report(summary, output_path)
        
        return filepath
    
    def save_markdown_report(self, summary: EvalSummary, output_dir: Path):
        """Save a markdown report of the evaluation."""
        filename = f"{summary.eval_id}_report.md"
        filepath = output_dir / filename
        
        report = f"""# Attendance Question Evaluation Report

**Eval ID:** {summary.eval_id}  
**Timestamp:** {summary.timestamp}  
**API URL:** {summary.api_url}

---

## 📊 Overall Results

| Metric | Value |
|--------|-------|
| Total Tests | {summary.total_tests} |
| Passed | {summary.passed} ✅ |
| Failed | {summary.failed} ❌ |
| Pass Rate | {summary.pass_rate:.1f}% |

## ⏱️ Response Time Statistics

| Metric | Value |
|--------|-------|
| Average | {summary.avg_response_time_ms:.0f}ms |
| Minimum | {summary.min_response_time_ms:.0f}ms |
| Maximum | {summary.max_response_time_ms:.0f}ms |
| P95 | {summary.p95_response_time_ms:.0f}ms |

## 📋 Results by Question Tone

| Tone | Pass Rate | Passed | Total | Avg Time |
|------|-----------|--------|-------|----------|
"""
        for tone, stats in summary.by_tone.items():
            status = "✅" if stats["pass_rate"] >= 80 else "⚠️" if stats["pass_rate"] >= 50 else "❌"
            report += f"| {status} {tone} | {stats['pass_rate']:.1f}% | {stats['passed']} | {stats['total']} | {stats['avg_response_time_ms']:.0f}ms |\n"
        
        # Add failed tests section
        failed_results = [r for r in summary.results if not r["success"]]
        if failed_results:
            report += f"\n## ❌ Failed Tests ({len(failed_results)})\n\n"
            for r in failed_results:
                report += f"### {r['test_case']['tone'].upper()}: {r['test_case']['question']}\n\n"
                if r.get("error"):
                    report += f"**Error:** `{r['error']}`\n\n"
                else:
                    report += f"**Missing Keywords:** {', '.join(r['keywords_missing'])}\n\n"
                    if r.get("response"):
                        response_preview = r['response'][:200] + "..." if len(r['response']) > 200 else r['response']
                        report += f"**Response Preview:**\n```\n{response_preview}\n```\n\n"
        
        # Add sample successful responses
        passed_results = [r for r in summary.results if r["success"]]
        if passed_results:
            report += f"\n## ✅ Sample Successful Responses (5)\n\n"
            for r in passed_results[:5]:
                report += f"### {r['test_case']['tone'].upper()}: {r['test_case']['question']}\n\n"
                response_preview = r['response'][:300] + "..." if len(r['response']) > 300 else r['response']
                report += f"**Response:**\n```\n{response_preview}\n```\n"
                report += f"**Response Time:** {r['response_time_ms']:.0f}ms  \n"
                report += f"**Keywords Found:** {', '.join(r['keywords_found'])}\n\n"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"📄 Markdown report saved to: {filepath}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate VoiceBot attendance question handling")
    parser.add_argument(
        "--api-url", 
        default="https://voicebot-kamaraj-v1.vercel.app",
        help="API URL to test against"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of concurrent requests"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of test cases (for quick testing)"
    )
    
    args = parser.parse_args()
    
    evaluator = AttendanceEvaluator(args.api_url)
    
    test_cases = ATTENDANCE_TEST_CASES
    if args.limit:
        test_cases = test_cases[:args.limit]
    
    summary = await evaluator.run_evaluation(test_cases, concurrency=args.concurrency)
    evaluator.print_summary(summary)
    evaluator.save_results(summary)


if __name__ == "__main__":
    asyncio.run(main())
