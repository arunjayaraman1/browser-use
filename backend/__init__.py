"""
Backend module for Amazon shopping automation.
"""
from backend.models import CartResult, ProductIntent, ProductItem
from backend.intent_parser import parse_intent
from backend.browser_agent import run_browser_agent

__all__ = [
    'CartResult',
    'ProductIntent',
    'ProductItem',
    'parse_intent',
    'run_browser_agent',
]
