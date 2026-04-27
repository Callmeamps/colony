#!/usr/bin/env python3
"""
Scout Performance Benchmark Suite
Target: <50ms classification per Phase 4 spec
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import sys
sys.path.insert(0, '.')

from core.cache import ScoutCache
from core.workers.scout import Scout


class ScoutBenchmark:
    """Comprehensive Scout performance benchmarking"""
    
    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.scout = None
        self.results = []
        
    async def setup(self):
        """Initialize Scout for testing"""
        # Use memory fallback for isolated testing
        cache = ScoutCache(redis_url="redis://invalid:6379/0", ttl_seconds=60)
        self.scout = Scout(pr=None, model_path=None, redis_url="redis://invalid:6379/0")
        
    def _get_test_prompts(self) -> List[str]:
        """Diverse test prompts covering different urgency patterns"""
        return [
            # High urgency (0.8-1.0)
            "Critical error in production server",
            "Emergency system crash need fix now",
            "Bug causing data loss help",
            "Service down customers affected",
            
            # Medium urgency (0.5-0.7)  
            "Performance issue in API endpoints",
            "Memory leak detected in worker",
            "Slow query optimization needed",
            "Cache invalidation problem",
            
            # Low urgency (0.1-0.4)
            "How to declare a variable in Python",
            "Difference between list and tuple",
            "Best practices for error handling",
            "Documentation update request",
            
            # Direct answer candidates (short, clear questions)
            "What is HTTP?",
            "Python string methods",
            "REST API definition",
            "Git commit message format"
        ]
    
    async def benchmark_urgency_scoring(self) -> Dict[str, Any]:
        """Benchmark urgency scoring path"""
        print("Benchmarking urgency scoring...")
        latencies = []
        
        prompts = self._get_test_prompts()
        
        for i in range(self.iterations):
            prompt = prompts[i % len(prompts)]
            
            start = time.perf_counter()
            result = await self.scout.classify(prompt)
            end = time.perf_counter()
            
            latencies.append((end - start) * 1000)  # Convert to ms
            
        stats = {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            "p99_ms": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
            "total_calls": len(latencies),
            "under_50ms": sum(1 for lat in latencies if lat <= 50),
            "under_50ms_pct": round(sum(1 for lat in latencies if lat <= 50) / len(latencies) * 100, 1)
        }
        
        return stats
    
    async def benchmark_direct_answer_path(self) -> Dict[str, Any]:
        """Benchmark direct answer detection path"""
        print("Benchmarking direct answer detection...")
        latencies = []
        
        # Questions that should trigger direct answer path
        direct_prompts = [
            "What is Python?",
            "How do I import modules?",
            "String concatenation in Python",
            "List vs tuple difference",
            "HTTP status codes"
        ]
        
        for i in range(self.iterations):
            prompt = direct_prompts[i % len(direct_prompts)]
            
            start = time.perf_counter()
            result = await self.scout.classify(prompt)
            end = time.perf_counter()
            
            latencies.append((end - start) * 1000)
            
        stats = {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p95_ms": statistics.quantiles(latencies, n=20)[18],
            "p99_ms": statistics.quantiles(latencies, n=100)[98],
            "total_calls": len(latencies),
            "direct_answers": sum(1 for i, result in enumerate(await self._get_results()) if result.get('can_answer_direct')),
            "under_50ms": sum(1 for lat in latencies if lat <= 50),
            "under_50ms_pct": round(sum(1 for lat in latencies if lat <= 50) / len(latencies) * 100, 1)
        }
        
        return stats
    
    async def benchmark_cache_performance(self) -> Dict[str, Any]:
        """Test cache hit/miss performance impact"""
        print("Benchmarking cache performance...")
        
        # First pass - cache misses (cold cache)
        cold_latencies = []
        test_prompt = "Critical production error needs fix"
        
        for i in range(10):  # Small number for cold cache
            start = time.perf_counter()
            await self.scout.classify(test_prompt)
            end = time.perf_counter()
            cold_latencies.append((end - start) * 1000)
        
        # Second pass - cache hits (warm cache)
        warm_latencies = []
        for i in range(50):
            start = time.perf_counter()
            await self.scout.classify(test_prompt)
            end = time.perf_counter()
            warm_latencies.append((end - start) * 1000)
        
        return {
            "cold_cache_avg_ms": statistics.mean(cold_latencies),
            "warm_cache_avg_ms": statistics.mean(warm_latencies),
            "cache_speedup_ms": statistics.mean(cold_latencies) - statistics.mean(warm_latencies),
            "cache_speedup_pct": round((statistics.mean(cold_latencies) - statistics.mean(warm_latencies)) / statistics.mean(cold_latencies) * 100, 1)
        }
    
    async def _get_results(self) -> List[Dict]:
        """Helper to collect classification results"""
        results = []
        prompts = self._get_test_prompts()
        
        for prompt in prompts[:5]:  # Small sample
            result = await self.scout.classify(prompt)
            results.append(result)
            
        return results
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("=== Scout Performance Benchmark ===")
        print(f"Iterations: {self.iterations}")
        print(f"Target: <50ms per classification")
        print()
        
        await self.setup()
        
        results = {
            "timestamp": time.time(),
            "iterations": self.iterations,
            "target_ms": 50,
            
            "urgency_scoring": await self.benchmark_urgency_scoring(),
            "direct_answer": await self.benchmark_direct_answer_path(),
            "cache_performance": await self.benchmark_cache_performance(),
            
            "scout_stats": await self.scout.get_stats() if hasattr(self.scout, 'get_stats') else {}
        }
        
        self._print_results(results)
        return results
    
    def _print_results(self, results: Dict[str, Any]):
        """Pretty print benchmark results"""
        print("\n=== RESULTS ===")
        
        # Urgency Scoring
        urgency = results["urgency_scoring"]
        print(f"Urgency Scoring:")
        print(f"  Average: {urgency['avg_ms']:.1f}ms")
        print(f"  Median:  {urgency['median_ms']:.1f}ms") 
        print(f"  P95:     {urgency['p95_ms']:.1f}ms")
        print(f"  Target:  <50ms {'✓' if urgency['avg_ms'] < 50 else '✗'}")
        print(f"  Under 50ms: {urgency['under_50ms']} ({urgency['under_50ms_pct']}%)")
        
        # Direct Answer
        direct = results["direct_answer"]
        print(f"\nDirect Answer Detection:")
        print(f"  Average: {direct['avg_ms']:.1f}ms")
        print(f"  P95:     {direct['p95_ms']:.1f}ms")
        print(f"  Target:  <50ms {'✓' if direct['avg_ms'] < 50 else '✗'}")
        print(f"  Under 50ms: {direct['under_50ms']} ({direct['under_50ms_pct']}%)")
        
        # Cache Performance
        cache = results["cache_performance"]
        print(f"\nCache Performance:")
        print(f"  Cold cache avg: {cache['cold_cache_avg_ms']:.1f}ms")
        print(f"  Warm cache avg: {cache['warm_cache_avg_ms']:.1f}ms")
        print(f"  Speedup: {cache['cache_speedup_ms']:.1f}ms ({cache['cache_speedup_pct']}%)")
        
        print(f"\nOverall: {'✓ PASS' if urgency['avg_ms'] < 50 and direct['avg_ms'] < 50 else '✗ FAIL'}")
