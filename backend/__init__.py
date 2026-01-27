"""
Backend module for Amazon shopping automation.
"""
from backend.models import CartResult, ProductIntent, ProductItem
from backend.browser_agent import run_browser_agent

__all__ = [
    'CartResult',
    'ProductIntent',
    'ProductItem',
    'run_browser_agent',
]
