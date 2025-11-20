"""
Custom error handling for generation operations.
Following GCP repo patterns.
"""


class GenerationError(Exception):
    """Custom exception for generation errors."""
    
    def __init__(self, message: str, error_type: str = "unknown"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)
