"""
AI Support Agent - Smart Caching System
LRU cache implementation with analytics and performance optimization
"""

import hashlib
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
from collections import OrderedDict
from dataclasses import asdict

from models import UserQuestion, SupportResponse, CacheEntry
from config import Config


class ResponseCache:
    """
    LRU (Least Recently Used) cache for storing question-response pairs
    Includes analytics, hit rate tracking, and intelligent cache management
    """
    
    def __init__(self, max_size: int = None, ttl_seconds: int = None):
        """
        Initialize the cache
        
        Args:
            max_size: Maximum number of cache entries
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size or Config.CACHE_MAX_SIZE
        self.ttl_seconds = ttl_seconds or Config.CACHE_TTL_SECONDS
        
        # Cache storage (LRU ordered dictionary)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Analytics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "ttl_expires": 0,
            "total_requests": 0
        }
        
        # Performance tracking
        self.start_time = datetime.now()
        self.hit_times: List[float] = []
        self.miss_times: List[float] = []
        
        # Background cleanup
        self._start_cleanup_thread()
    
    def get(self, question: UserQuestion) -> Optional[SupportResponse]:
        """
        Get cached response for a question
        
        Args:
            question: UserQuestion to look up
            
        Returns:
            Cached SupportResponse if found, None otherwise
        """
        start_time = time.perf_counter()
        
        with self._lock:
            self.stats["total_requests"] += 1
            
            # Generate cache key
            cache_key = self._generate_cache_key(question)
            
            # Check if entry exists
            if cache_key not in self._cache:
                self._record_miss(start_time)
                return None
            
            entry = self._cache[cache_key]
            
            # Check TTL
            if self._is_expired(entry):
                del self._cache[cache_key]
                self.stats["ttl_expires"] += 1
                self._record_miss(start_time)
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            
            # Update access tracking
            entry.access()
            
            # Record hit
            self._record_hit(start_time)
            
            return entry.response
    
    def put(self, question: UserQuestion, response: SupportResponse) -> None:
        """
        Store a question-response pair in cache
        
        Args:
            question: UserQuestion that was asked
            response: SupportResponse that was generated
        """
        with self._lock:
            # Generate cache key
            cache_key = self._generate_cache_key(question)
            
            # Create cache entry
            entry = CacheEntry(
                question_hash=cache_key,
                question_text=question.text,
                response=response
            )
            
            # Check if we need to evict entries
            while len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Store entry
            self._cache[cache_key] = entry
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
    
    def invalidate(self, question: UserQuestion) -> bool:
        """
        Remove a specific entry from cache
        
        Args:
            question: UserQuestion to remove
            
        Returns:
            True if entry was found and removed, False otherwise
        """
        with self._lock:
            cache_key = self._generate_cache_key(question)
            
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._reset_stats()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self.stats["ttl_expires"] += 1
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            total_requests = self.stats["total_requests"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate average response times
            avg_hit_time = sum(self.hit_times) / len(self.hit_times) if self.hit_times else 0
            avg_miss_time = sum(self.miss_times) / len(self.miss_times) if self.miss_times else 0
            
            # Cache utilization
            utilization = (len(self._cache) / self.max_size * 100) if self.max_size > 0 else 0
            
            # Most accessed entries
            top_entries = sorted(
                [(entry.question_text, entry.hit_count) for entry in self._cache.values()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "utilization_percent": utilization,
                "hit_rate_percent": hit_rate,
                "total_requests": total_requests,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "ttl_expires": self.stats["ttl_expires"],
                "average_hit_time_ms": avg_hit_time * 1000,
                "average_miss_time_ms": avg_miss_time * 1000,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "top_cached_questions": top_entries
            }
    
    def get_cache_efficiency(self) -> Dict[str, float]:
        """Calculate cache efficiency metrics"""
        with self._lock:
            total_requests = self.stats["total_requests"]
            
            if total_requests == 0:
                return {
                    "hit_rate": 0.0,
                    "miss_rate": 0.0,
                    "efficiency_score": 0.0
                }
            
            hit_rate = self.stats["hits"] / total_requests
            miss_rate = self.stats["misses"] / total_requests
            
            # Efficiency score considers hit rate and cache utilization
            utilization = len(self._cache) / self.max_size if self.max_size > 0 else 0
            efficiency_score = (hit_rate * 0.7) + (utilization * 0.3)
            
            return {
                "hit_rate": hit_rate,
                "miss_rate": miss_rate,
                "efficiency_score": efficiency_score,
                "cache_utilization": utilization
            }
    
    def get_popular_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed questions"""
        with self._lock:
            entries = [
                {
                    "question": entry.question_text,
                    "hit_count": entry.hit_count,
                    "last_accessed": entry.last_accessed.isoformat(),
                    "created_at": entry.created_at.isoformat()
                }
                for entry in self._cache.values()
            ]
            
            # Sort by hit count
            entries.sort(key=lambda x: x["hit_count"], reverse=True)
            
            return entries[:limit]
    
    def optimize_cache(self) -> Dict[str, int]:
        """
        Optimize cache by removing low-value entries
        
        Returns:
            Dictionary with optimization results
        """
        with self._lock:
            initial_size = len(self._cache)
            
            # Remove entries that haven't been accessed recently
            cutoff_time = datetime.now() - timedelta(hours=1)
            stale_keys = []
            
            for key, entry in self._cache.items():
                if entry.last_accessed < cutoff_time and entry.hit_count <= 1:
                    stale_keys.append(key)
            
            for key in stale_keys:
                del self._cache[key]
            
            # Remove low-hit entries if cache is still too full
            if len(self._cache) > self.max_size * 0.8:
                entries_by_hits = sorted(
                    self._cache.items(),
                    key=lambda x: x[1].hit_count
                )
                
                # Remove bottom 20% of entries by hit count
                remove_count = int(len(entries_by_hits) * 0.2)
                for key, _ in entries_by_hits[:remove_count]:
                    if key in self._cache:  # Double-check it's still there
                        del self._cache[key]
            
            final_size = len(self._cache)
            
            return {
                "initial_size": initial_size,
                "final_size": final_size,
                "removed_stale": len(stale_keys),
                "removed_low_hit": initial_size - final_size - len(stale_keys),
                "space_freed": initial_size - final_size
            }
    
    def _generate_cache_key(self, question: UserQuestion) -> str:
        """Generate a cache key for a question"""
        # Normalize question text for consistent caching
        normalized_text = question.text.lower().strip()
        
        # Remove extra whitespace
        normalized_text = " ".join(normalized_text.split())
        
        # Create hash
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired"""
        if self.ttl_seconds <= 0:
            return False  # No TTL
        
        age = datetime.now() - entry.created_at
        return age.total_seconds() > self.ttl_seconds
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._cache:
            self._cache.popitem(last=False)  # Remove first (oldest) item
            self.stats["evictions"] += 1
    
    def _record_hit(self, start_time: float) -> None:
        """Record a cache hit"""
        response_time = time.perf_counter() - start_time
        self.stats["hits"] += 1
        self.hit_times.append(response_time)
        
        # Keep only recent timing data
        if len(self.hit_times) > 1000:
            self.hit_times = self.hit_times[-500:]
    
    def _record_miss(self, start_time: float) -> None:
        """Record a cache miss"""
        response_time = time.perf_counter() - start_time
        self.stats["misses"] += 1
        self.miss_times.append(response_time)
        
        # Keep only recent timing data
        if len(self.miss_times) > 1000:
            self.miss_times = self.miss_times[-500:]
    
    def _reset_stats(self) -> None:
        """Reset all statistics"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "ttl_expires": 0,
            "total_requests": 0
        }
        self.hit_times.clear()
        self.miss_times.clear()
        self.start_time = datetime.now()
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    self.cleanup_expired()
                    
                    # Optimize cache periodically
                    if len(self._cache) > self.max_size * 0.9:
                        self.optimize_cache()
                        
                except Exception:
                    pass  # Ignore cleanup errors
        
        cleanup_thread = threading.Thread(
            target=cleanup_worker,
            daemon=True,
            name="CacheCleanup"
        )
        cleanup_thread.start()
    
    def export_cache_data(self) -> Dict[str, Any]:
        """Export cache data for persistence"""
        with self._lock:
            cache_data = {}
            
            for key, entry in self._cache.items():
                cache_data[key] = {
                    "question_text": entry.question_text,
                    "response": asdict(entry.response),
                    "hit_count": entry.hit_count,
                    "created_at": entry.created_at.isoformat(),
                    "last_accessed": entry.last_accessed.isoformat()
                }
            
            return {
                "cache_entries": cache_data,
                "stats": self.stats.copy(),
                "exported_at": datetime.now().isoformat()
            }
    
    def import_cache_data(self, data: Dict[str, Any]) -> int:
        """
        Import cache data from external source
        
        Args:
            data: Cache data dictionary
            
        Returns:
            Number of entries imported
        """
        with self._lock:
            imported_count = 0
            cache_entries = data.get("cache_entries", {})
            
            for key, entry_data in cache_entries.items():
                try:
                    # Reconstruct cache entry
                    response_data = entry_data["response"]
                    response = SupportResponse(**response_data)
                    
                    entry = CacheEntry(
                        question_hash=key,
                        question_text=entry_data["question_text"],
                        response=response,
                        hit_count=entry_data.get("hit_count", 0),
                        created_at=datetime.fromisoformat(entry_data["created_at"]),
                        last_accessed=datetime.fromisoformat(entry_data["last_accessed"])
                    )
                    
                    # Check if entry is still valid (not expired)
                    if not self._is_expired(entry):
                        self._cache[key] = entry
                        imported_count += 1
                    
                    # Respect max size
                    if len(self._cache) >= self.max_size:
                        break
                        
                except Exception:
                    continue  # Skip invalid entries
            
            return imported_count
    
    def __len__(self) -> int:
        """Get current cache size"""
        return len(self._cache)
    
    def __contains__(self, question: UserQuestion) -> bool:
        """Check if question is in cache"""
        cache_key = self._generate_cache_key(question)
        with self._lock:
            return cache_key in self._cache