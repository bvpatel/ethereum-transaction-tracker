import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from src.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality"""

    def test_init_default_rate(self):
        """Test RateLimiter initialization with default rate"""
        limiter = RateLimiter()
        assert limiter.calls_per_second == 5.0
        assert limiter.min_interval == 0.2
        assert limiter.last_call == 0.0
        assert isinstance(limiter._lock, asyncio.Lock)

    def test_init_custom_rate(self):
        """Test RateLimiter initialization with custom rate"""
        limiter = RateLimiter(calls_per_second=10.0)
        assert limiter.calls_per_second == 10.0
        assert limiter.min_interval == 0.1
        assert limiter.last_call == 0.0

    def test_init_fractional_rate(self):
        """Test RateLimiter initialization with fractional rate"""
        limiter = RateLimiter(calls_per_second=2.5)
        assert limiter.calls_per_second == 2.5
        assert limiter.min_interval == 0.4
        assert limiter.last_call == 0.0

    @pytest.mark.asyncio
    async def test_first_call_no_wait(self):
        """Test that first call doesn't wait"""
        limiter = RateLimiter(calls_per_second=5.0)
        
        start_time = time.time()
        await limiter.wait()
        end_time = time.time()
        
        # First call should be immediate (allowing small tolerance for execution time)
        assert end_time - start_time < 0.01
        assert limiter.last_call > 0

    @pytest.mark.asyncio
    async def test_second_call_waits(self):
        """Test that second call waits appropriate time"""
        limiter = RateLimiter(calls_per_second=5.0)  # 0.2s interval
        
        # First call
        await limiter.wait()
        first_call_time = limiter.last_call
        
        # Second call immediately after
        start_time = time.time()
        await limiter.wait()
        end_time = time.time()
        
        # Should have waited approximately 0.2 seconds
        wait_time = end_time - start_time
        assert 0.18 <= wait_time <= 0.22  # Allow small tolerance
        assert limiter.last_call > first_call_time

    @pytest.mark.asyncio
    async def test_calls_with_sufficient_gap_no_wait(self):
        """Test that calls with sufficient time gap don't wait"""
        limiter = RateLimiter(calls_per_second=5.0)  # 0.2s interval
        
        # First call
        await limiter.wait()
        
        # Wait longer than min_interval
        await asyncio.sleep(0.25)
        
        # Second call should not wait
        start_time = time.time()
        await limiter.wait()
        end_time = time.time()
        
        assert end_time - start_time < 0.01

    @pytest.mark.asyncio
    async def test_multiple_rapid_calls(self):
        """Test multiple rapid calls are properly rate limited"""
        limiter = RateLimiter(calls_per_second=10.0)  # 0.1s interval
        
        start_time = time.time()
        
        # Make 3 rapid calls
        for _ in range(3):
            await limiter.wait()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take approximately 0.2s (2 intervals for 3 calls)
        assert 0.18 <= total_time <= 0.22

    @pytest.mark.asyncio
    async def test_concurrent_calls_thread_safety(self):
        """Test that concurrent calls are handled safely"""
        limiter = RateLimiter(calls_per_second=10.0)  # 0.1s interval
        
        start_time = time.time()
        
        # Create multiple concurrent tasks
        tasks = [limiter.wait() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take approximately 0.4s (4 intervals for 5 calls)
        assert 0.35 <= total_time <= 0.45

    @pytest.mark.asyncio
    async def test_very_low_rate_limit(self):
        """Test with very low rate limit"""
        limiter = RateLimiter(calls_per_second=0.5)  # 2s interval
        
        start_time = time.time()
        
        # Make 2 calls
        await limiter.wait()
        await limiter.wait()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take approximately 2s
        assert 1.95 <= total_time <= 2.05

    @pytest.mark.asyncio
    async def test_very_high_rate_limit(self):
        """Test with very high rate limit"""
        limiter = RateLimiter(calls_per_second=100.0)  # 0.01s interval
        
        start_time = time.time()
        
        # Make 5 calls
        for _ in range(5):
            await limiter.wait()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should take approximately 0.04s (4 intervals)
        assert 0.035 <= total_time <= 0.05

    def test_lock_is_asyncio_lock(self):
        """Test that the lock is properly initialized as asyncio.Lock"""
        limiter = RateLimiter()
        assert isinstance(limiter._lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_last_call_updates_correctly(self):
        """Test that last_call timestamp updates correctly"""
        limiter = RateLimiter(calls_per_second=5.0)
        
        initial_last_call = limiter.last_call
        assert initial_last_call == 0.0
        
        before_call = time.time()
        await limiter.wait()
        after_call = time.time()
        
        # last_call should be updated to a time between before and after
        assert before_call <= limiter.last_call <= after_call

    @pytest.mark.asyncio
    async def test_rate_limiter_with_zero_rate(self):
        """Test edge case with very small rate"""
        # This tests behavior with very restrictive rate limiting
        limiter = RateLimiter(calls_per_second=0.1)  # 10s interval
        
        start_time = time.time()
        await limiter.wait()  # First call should be immediate
        first_call_time = time.time()
        
        # Verify first call was immediate
        assert first_call_time - start_time < 0.01
        
        # Note: We don't test the second call here as it would take 10 seconds


@pytest.mark.asyncio
class TestRateLimiterIntegration:
    """Integration tests for RateLimiter"""
    
    async def test_realistic_api_simulation(self):
        """Simulate realistic API usage pattern"""
        limiter = RateLimiter(calls_per_second=3.0)  # 0.333s interval
        
        call_times = []
        
        # Simulate making 4 API calls
        for i in range(4):
            start = time.time()
            await limiter.wait()
            call_times.append(time.time() - start)
        
        # First call should be immediate
        assert call_times[0] < 0.01
        
        # Subsequent calls should wait approximately 0.333s each
        for wait_time in call_times[1:]:
            assert 0.30 <= wait_time <= 0.37

    async def test_burst_then_pause_pattern(self):
        """Test burst of calls followed by pause"""
        limiter = RateLimiter(calls_per_second=5.0)  # 0.2s interval
        
        # Burst of 3 calls
        start_time = time.time()
        for _ in range(3):
            await limiter.wait()
        burst_time = time.time() - start_time
        
        # Should take ~0.4s for 3 calls
        assert 0.35 <= burst_time <= 0.45
        
        # Wait longer than rate limit
        await asyncio.sleep(0.5)
        
        # Next call should be immediate
        start_time = time.time()
        await limiter.wait()
        immediate_time = time.time() - start_time
        
        assert immediate_time < 0.01