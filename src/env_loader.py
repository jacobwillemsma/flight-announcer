#!/usr/bin/env python3
"""
Environment Variable Loader
Simple .env file loader compatible with both CircuitPython and desktop Python.
"""

import os

def load_env_file(env_path=".env"):
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file (relative to project root)
        
    Returns:
        dict: Environment variables as key-value pairs
    """
    env_vars = {}
    
    try:
        # For desktop Python, try to find .env in parent directories
        if not os.path.exists(env_path):
            # Look for .env in parent directory (when running from src/)
            parent_env = os.path.join("..", env_path)
            if os.path.exists(parent_env):
                env_path = parent_env
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            env_vars[key] = value
        
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")
    
    return env_vars

def get_env_var(key, default=None, env_vars=None):
    """
    Get an environment variable with fallback to .env file.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        env_vars: Pre-loaded env vars dict (optional)
        
    Returns:
        str: Environment variable value or default
    """
    # First try system environment variables
    value = os.environ.get(key)
    if value is not None:
        return value
    
    # Then try .env file
    if env_vars is None:
        env_vars = load_env_file()
    
    return env_vars.get(key, default)

def get_bool_env(key, default=False, env_vars=None):
    """Get a boolean environment variable."""
    value = get_env_var(key, str(default).lower(), env_vars)
    return value.lower() in ('true', '1', 'yes', 'on')

# Global env vars cache for efficiency
_env_cache = None

def get_cached_env():
    """Get cached environment variables."""
    global _env_cache
    if _env_cache is None:
        _env_cache = load_env_file()
    return _env_cache