import pytest
import asyncio
import time
from src.utils.rate_limiter import RateLimiter

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_delay(self):
        """Test that rate limiter introduces appropriate delays"""
        limiter = RateLimiter(calls_per_second=2)  # 0.5 seconds between calls
        
        start_time = time.time()
        
        # Make two calls
        await limiter.wait()
        await limiter.wait()
        
        elapsed = time.time() - start_time
        
        # Should take at least 0.5 seconds for the second call
        assert elapsed >= 0.4  # Allow some margin for timing variance

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_calls(self):
        """Test rate limiter with concurrent calls"""
        limiter = RateLimiter(calls_per_second=1)  # 1 second between calls
        
        start_time = time.time()
        
        # Make 3 concurrent calls
        tasks = [limiter.wait() for _ in range(3)]
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Should take at least 2 seconds for 3 calls with 1 call/second
        assert elapsed >= 1.8