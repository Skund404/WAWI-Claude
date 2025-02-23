# utils/performance_tracker.py
"""
Performance Tracking Utility for Store Management System.

Provides decorators and utilities for measuring and logging
method performance and caching statistics.
"""

import time
import functools
import logging
from typing import Any, Callable, Dict
from collections import defaultdict


class PerformanceTracker:
    """
    Comprehensive performance tracking and analysis utility.

    Tracks method invocations, execution times, cache hits/misses,
    and provides detailed performance insights.
    """

    def __init__(self, log_level=logging.INFO):
        """
        Initialize Performance Tracker.

        Args:
            log_level (int): Logging level for performance metrics
        """
        self.logger = logging.getLogger('performance_tracker')
        self.logger.setLevel(log_level)

        # Performance metrics storage
        self.method_metrics = defaultdict(lambda: {
            'total_calls': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        })

    def track_performance(self, cache_enabled: bool = False):
        """
        Decorator to track method performance and optional caching.

        Args:
            cache_enabled (bool): Enable caching for the method

        Returns:
            Callable: Decorated method with performance tracking
        """

        def decorator(func: Callable) -> Callable:
            # Create a cache if enabled
            if cache_enabled:
                cache = {}

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key if caching is enabled
                if cache_enabled:
                    cache_key = str(args) + str(kwargs)

                    # Check cache
                    if cache_key in cache:
                        self.method_metrics[func.__name__]['cache_hits'] += 1
                        return cache[cache_key]

                    self.method_metrics[func.__name__]['cache_misses'] += 1

                # Track method performance
                start_time = time.perf_counter()

                try:
                    # Execute the method
                    result = func(*args, **kwargs)

                    # Calculate execution time
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time

                    # Update method metrics
                    metrics = self.method_metrics[func.__name__]
                    metrics['total_calls'] += 1
                    metrics['total_time'] += execution_time
                    metrics['avg_time'] = metrics['total_time'] / metrics['total_calls']

                    # Log performance if threshold is exceeded
                    if execution_time > 0.1:  # Log methods taking more than 100ms
                        self.logger.warning(
                            f"Slow method: {func.__name__} "
                            f"took {execution_time:.4f} seconds"
                        )

                    # Cache the result if caching is enabled
                    if cache_enabled:
                        cache[cache_key] = result

                    return result

                except Exception as e:
                    # Log any exceptions during method execution
                    self.logger.error(
                        f"Error in method {func.__name__}: {e}"
                    )
                    raise

            return wrapper

        return decorator

    def get_method_metrics(self, method_name: str = None) -> Dict[str, Any]:
        """
        Retrieve performance metrics for a specific method or all methods.

        Args:
            method_name (str, optional): Name of the method to retrieve metrics for

        Returns:
            Dict[str, Any]: Performance metrics
        """
        if method_name:
            return self.method_metrics.get(method_name, {})
        return dict(self.method_metrics)

    def reset_metrics(self, method_name: str = None):
        """
        Reset performance metrics.

        Args:
            method_name (str, optional): Specific method to reset, or all if None
        """
        if method_name:
            if method_name in self.method_metrics:
                del self.method_metrics[method_name]
        else:
            self.method_metrics.clear()

    def generate_performance_report(self) -> str:
        """
        Generate a comprehensive performance report.

        Returns:
            str: Formatted performance report
        """
        report = ["Performance Metrics Report", "=" * 30]

        for method, metrics in self.method_metrics.items():
            report.append(f"\nMethod: {method}")
            report.append(f"  Total Calls: {metrics['total_calls']}")
            report.append(f"  Total Execution Time: {metrics['total_time']:.4f} seconds")
            report.append(f"  Average Execution Time: {metrics['avg_time']:.4f} seconds")

            if 'cache_hits' in metrics:
                report.append(f"  Cache Hits: {metrics['cache_hits']}")
                report.append(f"  Cache Misses: {metrics['cache_misses']}")

                # Calculate cache hit ratio
                total_cache_calls = metrics['cache_hits'] + metrics['cache_misses']
                if total_cache_calls > 0:
                    hit_ratio = metrics['cache_hits'] / total_cache_calls * 100
                    report.append(f"  Cache Hit Ratio: {hit_ratio:.2f}%")

        return "\n".join(report)


# Global performance tracker instance
PERFORMANCE_TRACKER = PerformanceTracker()