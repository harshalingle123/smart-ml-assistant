"""
Memory management utilities for production environments with limited RAM
"""
import gc
import os
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Make psutil optional (may not be available in all environments)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - memory usage monitoring disabled")


def get_memory_usage():
    """Get current memory usage in MB (requires psutil)"""
    if not PSUTIL_AVAILABLE:
        return 0.0
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)  # Convert to MB
    except Exception as e:
        logger.warning(f"Failed to get memory usage: {e}")
        return 0.0


def force_garbage_collection():
    """Force garbage collection to free up memory"""
    gc.collect()
    memory = get_memory_usage()
    if memory > 0:
        logger.info(f"Garbage collection completed. Current memory: {memory:.2f} MB")
    else:
        logger.debug("Garbage collection completed")


def memory_cleanup(func):
    """
    Decorator to clean up memory after function execution
    Use this for memory-intensive operations like dataset loading
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Log memory before
        memory_before = get_memory_usage()
        logger.info(f"[{func.__name__}] Memory before: {memory_before:.2f} MB")

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            # Force cleanup after operation
            force_garbage_collection()
            memory_after = get_memory_usage()
            logger.info(f"[{func.__name__}] Memory after: {memory_after:.2f} MB (freed: {memory_before - memory_after:.2f} MB)")

    return wrapper


def check_memory_threshold(threshold_mb: int = 400):
    """
    Check if memory usage exceeds threshold (in MB)
    Raise warning if threshold exceeded
    """
    current_memory = get_memory_usage()
    if current_memory > threshold_mb:
        logger.warning(f"Memory usage high: {current_memory:.2f} MB (threshold: {threshold_mb} MB)")
        force_garbage_collection()
        return False
    return True


def log_memory_usage(operation: str):
    """Log current memory usage with context"""
    memory_mb = get_memory_usage()
    if memory_mb > 0:
        logger.info(f"[MEMORY] {operation}: {memory_mb:.2f} MB")
        print(f"[MEMORY] {operation}: {memory_mb:.2f} MB")
    return memory_mb
