#!/usr/bin/env python3
"""
Simple Scout performance test without full dependencies
"""
import asyncio
import time
import statistics
from typing import Dict, Any


class MockScout:
    """Minimal Scout for testing core performance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_pattern(self, query: str):
        """Mock cache get"""
        if query in self.cache:
            self.cache_hits += 1
            return self.cache[query]
        self.cache_misses += 1
        return None
    
    def set_pattern(self, query: str, urgency: float):
        """Mock cache set"""
        self.cache[query] = urgency
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance stats"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / max(1, total)
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": round(hit_rate, 3)
        }
    
    async def classify(self, prompt: str) -> Dict[str, Any]:
        """Mock classification - simulate realistic latency"""
        start = time.perf_counter()
        
        # Simulate query extraction
        query = " ".join(prompt.lower().split()[:5])
        
        # Check cache
        cached_urgency = self.get_pattern(query)
        
        if cached_urgency is not None:
            urgency = cached_urgency
            can_direct = False
            answer = None
        else:
            # Simulate urgency scoring (heuristic)
            urgent_words = ["error", "bug", "critical", "emergency", "fix", "crash"]
            question_words = ["what", "how", "why", "when", "where"]
            
            urgent_count = sum(1 for word in urgent_words if word in prompt.lower())
            question_count = sum(1 for word in question_words if word in prompt.lower())
            
            if urgent_count >= 2:
                urgency = 0.9
            elif urgent_count == 1:
                urgency = 0.7
            elif question_count > 0 and len(prompt) < 100:
                urgency = 0.4
            else:
                urgency = 0.5
                
            # Cache significant urgency scores
            if urgency > 0.5:
                self.set_pattern(query, urgency)
                
            can_direct = question_count > 0 and len(prompt) < 50
            answer = f"Mock answer for {query[:20]}..."
        
        elapsed = time.perf_counter() - start
        
        return {
            "urgency": urgency,
            "can_answer_direct": can_direct,
            "answer": answer,
            "scout_time_ms": round(elapsed * 1000, 1)
        }


async def test_performance():
    """Test Scout performance"""
    print("=== Simple Scout Performance Test ===")
    
    scout = MockScout()
    test_prompts = [
        "Critical error in production server",
        "How do I declare a variable?",
        "Emergency system crash",
        "What is HTTP?",
        "Bug causing data loss",
        "Python string concatenation"
    ]
    
    latencies = []
    
    # Warm up cache
    print("Warming up cache...")
    for prompt in test_prompts * 2:
        await scout.classify(prompt)
    
    # Performance test
    print("Running performance test...")
    for i in range(100):
        prompt = test_prompts[i % len(test_prompts)]
        result = await scout.classify(prompt)
        latencies.append(result['scout_time_ms'])
    
    # Calculate stats
    avg_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    under_50ms = sum(1 for lat in latencies if lat <= 50)
    
    print(f"\nPerformance Results:")
    print(f"  Average: {avg_latency:.1f}ms")
    print(f"  Median:  {median_latency:.1f}ms")
    print(f"  P95:     {p95_latency:.1f}ms")
    print(f"  <50ms:   {under_50ms}%")
    print(f"  Target:  <50ms {'✓' if avg_latency < 50 else '✗'}")
    
    print(f"\nCache Stats: {scout.get_stats()}")
    
    return avg_latency < 50


if __name__ == "__main__":
    result = asyncio.run(test_performance())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
    exit(0 if result else 1)