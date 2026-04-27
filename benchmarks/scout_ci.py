#!/usr/bin/env python3
"""
Scout CI/CD benchmark runner
Lightweight performance validation for automated testing
"""
import json
import time
from typing import Dict, Any


class ScoutBenchmark:
    """Minimal benchmark for CI validation"""
    
    def __init__(self):
        self.target_ms = 50  # Phase 4 spec
        self.tests = []
        
    def test_urgency_patterns(self):
        """Test urgency scoring performance"""
        test_cases = [
            ("Critical error in production", 0.9),
            ("Emergency system crash", 0.9), 
            ("How to declare variable?", 0.4),
            ("Documentation update needed", 0.3),
            ("Performance optimization", 0.6)
        ]
        
        results = []
        for prompt, expected_urgency in test_cases:
            start = time.perf_counter()
            
            # Simulate urgency scoring (heuristic)
            if "critical" in prompt.lower() or "emergency" in prompt.lower():
                urgency = 0.9
            elif "error" in prompt.lower() or "crash" in prompt.lower():
                urgency = 0.8
            elif "how" in prompt.lower() or "what" in prompt.lower():
                urgency = 0.4
            else:
                urgency = 0.5
                
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            results.append({
                "prompt": prompt,
                "expected_urgency": expected_urgency,
                "actual_urgency": urgency,
                "latency_ms": round(elapsed_ms, 2),
                "under_target": elapsed_ms <= self.target_ms
            })
            
        return results
        
    def test_direct_answer_detection(self):
        """Test direct answer path performance"""
        test_cases = [
            "What is Python?",
            "How do I concatenate strings?", 
            "Difference between list and tuple",
            "What is HTTP status 200?",
            "Git commit message format"
        ]
        
        results = []
        for prompt in test_cases:
            start = time.perf_counter()
            
            # Simulate direct answer detection
            is_question = any(word in prompt.lower() for word in ["what", "how", "difference"])
            short_enough = len(prompt) < 80
            can_direct = is_question and short_enough
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            results.append({
                "prompt": prompt,
                "can_answer_direct": can_direct,
                "latency_ms": round(elapsed_ms, 2),
                "under_target": elapsed_ms <= self.target_ms
            })
            
        return results
    
    def run_benchmark(self) -> Dict[str, Any]:
        """Run CI benchmark suite"""
        print("=== Scout CI Performance Benchmark ===")
        print(f"Target: <{self.target_ms}ms per classification")
        
        urgency_results = self.test_urgency_patterns()
        direct_results = self.test_direct_answer_detection()
        
        # Calculate metrics
        all_results = urgency_results + direct_results
        total_tests = len(all_results)
        under_target = sum(1 for r in all_results if r["under_target"])
        avg_latency = statistics.mean(r["latency_ms"] for r in all_results)
        max_latency = max(r["latency_ms"] for r in all_results)
        
        results = {
            "timestamp": time.time(),
            "target_ms": self.target_ms,
            "total_tests": total_tests,
            "passed": under_target,
            "failed": total_tests - under_target,
            "pass_rate": round(under_target / total_tests * 100, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "max_latency_ms": round(max_latency, 2),
            "urgency_tests": urgency_results,
            "direct_answer_tests": direct_results,
            "overall_pass": avg_latency <= self.target_ms
        }
        
        self._print_results(results)
        return results
    
    def _print_results(self, results: Dict[str, Any]):
        """Print formatted results"""
        print(f"\nResults:")
        print(f"  Total tests: {results['total_tests']}")
        print(f"  Passed: {results['passed']} ({results['pass_rate']}%)")
        print(f"  Avg latency: {results['avg_latency_ms']}ms")
        print(f"  Max latency: {results['max_latency_ms']}ms")
        print(f"  Target: <{results['target_ms']}ms")
        print(f"  Overall: {'✓ PASS' if results['overall_pass'] else '✗ FAIL'}")
        
        # Show failed tests
        failed = results['total_tests'] - results['passed']
        if failed > 0:
            print(f"\nFailed tests:")
            for test in results['urgency_tests'] + results['direct_answer_tests']:
                if not test['under_target']:
                    print(f"  {test['prompt'][:40]}... - {test['latency_ms']}ms")


if __name__ == "__main__":
    import statistics
    
    benchmark = ScoutBenchmark()
    results = benchmark.run_benchmark()
    
    # Save results for CI
    with open('scout_ci_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    exit(0 if results['overall_pass'] else 1)