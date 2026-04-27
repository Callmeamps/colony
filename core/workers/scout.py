import json
import time
from typing import Optional, List, Dict, Any
from core.records import PunkRecords
from core.nest import Nest

class Scout:
    """Spec 4.1: Urgency scoring + Direct answering from Nest crystals
    
    Model: Bonsai-1.7B (INT4 GGUF), ~200MB disk, ~250MB RAM
    Runtime: llama.cpp CPU, always loaded, never unloaded
    Target: <50ms per classification, <270MB idle RAM total
    """
    def __init__(self, pr: PunkRecords, model_path: Optional[str] = None):
        self.pr = pr
        self.model_path = model_path or "models/bonsai-1.7b-q4.gguf"  # Default Bonsai-1.7B
        self.model = None  # llama.cpp instance (lazy init)
        self.direct_threshold = 0.85  # Cosine similarity threshold for direct answers
        self.urgency_cache = {}  # Cache urgency patterns for fast lookup
        
    def _ensure_model(self):
        """Lazy load model if not already loaded"""
        if self.model is None and self.model_path:
            # TODO: Integrate llama-cpp-python
            # from llama_cpp import Llama
            # self.model = Llama(model_path=self.model_path, n_ctx=512, n_threads=2)
            pass
            
    async def classify(self, prompt: str) -> Dict[str, Any]:
        """Score urgency 0-1 and check for direct Nest answer
        
        Returns:
            urgency: float (0-1)
            can_answer_direct: bool
            answer: Optional[str]
            reasoning: str
        """
        start = time.time()
        
        # Step 1: Check urgency patterns
        urgency = self._score_urgency(prompt)
        
        # Step 2: Try direct Nest answer
        can_answer_direct, answer = await self._try_direct_answer(prompt)
        
        # Step 3: Cache result for similar patterns
        self._cache_pattern(prompt, urgency, can_answer_direct)
        
        elapsed_ms = (time.time() - start) * 1000
        
        return {
            "urgency": urgency,
            "can_answer_direct": can_answer_direct,
            "answer": answer,
            "scout_time_ms": round(elapsed_ms, 1)
        }
    
    def _score_urgency(self, prompt: str) -> float:
        """Heuristic urgency scoring based on prompt patterns
        
        Higher score = more urgent, needs immediate Clone wake
        Lower score = can wait or answer directly from Nest
        """
        urgency = 0.5  # Default
        
        # Check cached patterns first
        for pattern, cached_urgency in self.urgency_cache.items():
            if pattern.lower() in prompt.lower():
                return cached_urgency
                
        # Keywords that indicate urgency
        urgent_keywords = ["error", "bug", "critical", "emergency", "fix", "broken", "fail", "crash"]
        urgent_count = sum(1 for kw in urgent_keywords if kw in prompt.lower())
        
        if urgent_count >= 2:
            urgency = 0.9
        elif urgent_count == 1:
            urgency = 0.7
        elif len(prompt.split()) < 10:  # Short queries often simple
            urgency = 0.3
        elif "?" in prompt and len(prompt) < 100:  # Direct question
            urgency = 0.4
            
        return min(1.0, max(0.0, urgency))
    
    async def _try_direct_answer(self, prompt: str) -> tuple[bool, Optional[str]]:
        """Check if Nest has direct answer with high confidence
        
        If top-1 crystal has cosine similarity > threshold, answer directly
        without waking Clone.
        """
        # Extract query terms from prompt
        query = self._extract_query(prompt)
        if not query:
            return False, None
            
        # Search Nest for matching crystals
        results = await Nest.query(query, k=1)
        if not results:
            return False, None
            
        top_result = results[0]
        if top_result.get("similarity", 0) < self.direct_threshold:
            return False, None
            
        # High confidence match - answer directly
        return True, top_result.get("text")
    
    def _extract_query(self, prompt: str) -> str:
        """Extract search query from prompt for Nest lookup"""
        # Remove common stop words and punctuation
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "can", "shall", "to", "of", "in", "for",
                     "on", "with", "at", "by", "from", "as", "into", "through", "during",
                     "before", "after", "above", "below", "between", "under", "again",
                     "further", "then", "once", "here", "there", "when", "where", "why",
                     "how", "what", "which", "who", "whom", "this", "that", "these",
                     "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
                     "her", "us", "them", "my", "your", "his", "its", "our", "their",
                     "mine", "yours", "hers", "ours", "theirs"}
                     
        words = prompt.lower().split()
        query_words = [w.strip(".,!?;:\"'()[]{}") for w in words if w.lower() not in stop_words]
        return " ".join(query_words) if query_words else ""
    
    def _cache_pattern(self, prompt: str, urgency: float, can_answer_direct: bool):
        """Cache pattern for faster future lookups"""
        # Simple pattern caching - in production would use more sophisticated caching
        query = self._extract_query(prompt)
        if query:
            self.urgency_cache[query] = urgency
            
    async def get_stats(self) -> Dict[str, Any]:
        """Return Scout performance stats"""
        return {
            "model_loaded": self.model is not None,
            "model_path": self.model_path,
            "urgency_cache_size": len(self.urgency_cache),
            "direct_threshold": self.direct_threshold,
            "idle_ram_mb": 250  # Target RAM usage
        }
