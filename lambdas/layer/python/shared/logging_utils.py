"""
Logging configuration for Lambda functions.
"""

import json
import logging
import time
from functools import wraps


def setup_logging(level=logging.INFO):
    """Configure structured JSON logging for Lambda."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove default Lambda handler to avoid duplicate logs
    for handler in logger.handlers:
        logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    return logger


def lambda_handler_wrapper(func):
    """
    Decorator for Lambda handlers that adds:
    - Structured logging setup
    - Timing
    - Error handling with proper response format
    """

    @wraps(func)
    def wrapper(event, context):
        logger = setup_logging()
        start = time.time()
        function_name = context.function_name if context else "local"

        logger.info(f"START {function_name}")

        try:
            result = func(event, context)
            elapsed = time.time() - start
            logger.info(f"END {function_name} ({elapsed:.1f}s)")

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "success": True,
                        "function": function_name,
                        "elapsed_seconds": round(elapsed, 1),
                        "result": result,
                    }
                ),
            }
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"FAIL {function_name} ({elapsed:.1f}s): {e}", exc_info=True)

            return {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "success": False,
                        "function": function_name,
                        "elapsed_seconds": round(elapsed, 1),
                        "error": str(e),
                    }
                ),
            }

    return wrapper
