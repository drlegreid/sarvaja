"""
Test Runner API Routes
Per WORKFLOW-SHELL-01-v1: Self-assessment via containerized tests
"""
from .runner import router as tests_router

__all__ = ["tests_router"]
