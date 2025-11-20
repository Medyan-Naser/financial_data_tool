"""
Modular Cache Manager

A flexible, customizable caching system that supports:
- JSON storage (human-readable)
- Configurable cache directories
- Configurable expiration times
- Multiple cache namespaces
- Easy integration across the project

Usage:
    from app.cache_manager import CacheManager
    
    # Create a cache instance
    stock_cache = CacheManager(
        namespace='stocks',
        expiry_hours=168,  # 1 week
        cache_dir='.api_cache/stocks'
    )
    
    # Store data
    stock_cache.set('AAPL_1y', data)
    
    # Retrieve data
    data = stock_cache.get('AAPL_1y')
    
    # Check if exists
    if stock_cache.exists('AAPL_1y'):
        print("Cache hit!")
"""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Modular cache manager with JSON storage
    """
    
    def __init__(
        self,
        namespace: str,
        expiry_hours: int = 168,  # 1 week default
        cache_dir: Optional[str] = None,
        auto_cleanup: bool = True
    ):
        """
        Initialize cache manager
        
        Args:
            namespace: Cache namespace (e.g., 'stocks', 'AI', 'economy')
            expiry_hours: Cache expiration time in hours
            cache_dir: Custom cache directory (default: .api_cache/{namespace})
            auto_cleanup: Automatically clean expired entries on init
        """
        self.namespace = namespace
        self.expiry_hours = expiry_hours
        self.expiry_delta = timedelta(hours=expiry_hours)
        
        # Set cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.cache_dir = project_root / '.api_cache' / namespace
        
        # Create directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Cache '{namespace}' initialized at: {self.cache_dir}")
        logger.info(f"Cache expiry: {expiry_hours} hours")
        
        # Auto cleanup expired entries
        if auto_cleanup:
            self.cleanup_expired()
    
    def _generate_key(self, key: str, **params) -> str:
        """
        Generate a descriptive cache key from parameters
        
        Args:
            key: Base key
            **params: Additional parameters to include in key
            
        Returns:
            Descriptive filename like "AAPL_1y_historical" or "health_score_AAPL_quarterly"
        """
        # Build descriptive filename from params
        parts = [key]
        
        # Add params in consistent order
        for param_key in sorted(params.keys()):
            value = str(params[param_key])
            # Clean value for filename (remove spaces, special chars)
            clean_value = value.replace(' ', '_').replace('/', '_').replace('\\', '_')
            parts.append(clean_value)
        
        # Join with underscores
        descriptive_key = '_'.join(parts)
        
        # Limit length and ensure valid filename
        if len(descriptive_key) > 100:
            # Keep first part and add hash for uniqueness
            hash_suffix = hashlib.md5(descriptive_key.encode()).hexdigest()[:8]
            descriptive_key = descriptive_key[:80] + '_' + hash_suffix
        
        return descriptive_key
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get full path to cache file"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get path to metadata file"""
        return self.cache_dir / f"{cache_key}.meta.json"
    
    def set(self, key: str, data: Any, **params) -> bool:
        """
        Store data in cache
        
        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
            **params: Additional parameters for key generation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._generate_key(key, **params)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_metadata_path(cache_key)
            
            # Store data
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Store metadata
            metadata = {
                'key': key,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'expiry': (datetime.now() + self.expiry_delta).isoformat(),
                'namespace': self.namespace
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Cached '{key}' with params {params}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache '{key}': {e}")
            return False
    
    def get(self, key: str, **params) -> Optional[Any]:
        """
        Retrieve data from cache
        
        Args:
            key: Cache key
            **params: Additional parameters for key generation
            
        Returns:
            Cached data if found and not expired, None otherwise
        """
        try:
            cache_key = self._generate_key(key, **params)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_metadata_path(cache_key)
            
            # Check if cache exists
            if not cache_path.exists() or not meta_path.exists():
                return None
            
            # Load metadata and check expiration
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            expiry = datetime.fromisoformat(metadata['expiry'])
            if datetime.now() > expiry:
                logger.debug(f"Cache expired for '{key}'")
                self.delete(key, **params)
                return None
            
            # Load and return data
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Cache hit for '{key}' with params {params}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to retrieve cache for '{key}': {e}")
            return None
    
    def exists(self, key: str, **params) -> bool:
        """Check if key exists in cache and is not expired"""
        return self.get(key, **params) is not None
    
    def delete(self, key: str, **params) -> bool:
        """
        Delete cached data
        
        Args:
            key: Cache key
            **params: Additional parameters for key generation
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache_key = self._generate_key(key, **params)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_metadata_path(cache_key)
            
            deleted = False
            if cache_path.exists():
                cache_path.unlink()
                deleted = True
            if meta_path.exists():
                meta_path.unlink()
                deleted = True
            
            if deleted:
                logger.debug(f"Deleted cache for '{key}'")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete cache for '{key}': {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries
        
        Returns:
            Number of entries removed
        """
        removed = 0
        try:
            for meta_file in self.cache_dir.glob("*.meta.json"):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    expiry = datetime.fromisoformat(metadata['expiry'])
                    if datetime.now() > expiry:
                        # Delete both data and metadata files
                        cache_key = meta_file.stem.replace('.meta', '')
                        cache_file = self.cache_dir / f"{cache_key}.json"
                        
                        if cache_file.exists():
                            cache_file.unlink()
                        meta_file.unlink()
                        removed += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to process {meta_file}: {e}")
                    continue
            
            if removed > 0:
                logger.info(f"Cleaned up {removed} expired cache entries in '{self.namespace}'")
            
            return removed
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")
            return 0
    
    def clear_all(self) -> int:
        """
        Clear all cache entries in this namespace
        
        Returns:
            Number of entries removed
        """
        removed = 0
        try:
            for file in self.cache_dir.glob("*.json"):
                file.unlink()
                removed += 1
            
            logger.info(f"Cleared {removed} cache files in '{self.namespace}'")
            return removed
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache info
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            meta_files = list(self.cache_dir.glob("*.meta.json"))
            data_files = [f for f in cache_files if not f.name.endswith('.meta.json')]
            
            total_size = sum(f.stat().st_size for f in cache_files)
            
            # Count valid (non-expired) entries
            valid_entries = 0
            expired_entries = 0
            
            for meta_file in meta_files:
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    expiry = datetime.fromisoformat(metadata['expiry'])
                    if datetime.now() > expiry:
                        expired_entries += 1
                    else:
                        valid_entries += 1
                except:
                    pass
            
            return {
                'namespace': self.namespace,
                'cache_dir': str(self.cache_dir),
                'total_entries': len(data_files),
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'expiry_hours': self.expiry_hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {}
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """
        List all cache keys with metadata
        
        Returns:
            List of dictionaries with key info
        """
        keys = []
        try:
            for meta_file in self.cache_dir.glob("*.meta.json"):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                    
                    expiry = datetime.fromisoformat(metadata['expiry'])
                    is_expired = datetime.now() > expiry
                    
                    cache_key = meta_file.stem.replace('.meta', '')
                    cache_file = self.cache_dir / f"{cache_key}.json"
                    size_kb = cache_file.stat().st_size / 1024 if cache_file.exists() else 0
                    
                    keys.append({
                        'key': metadata.get('key'),
                        'params': metadata.get('params', {}),
                        'timestamp': metadata.get('timestamp'),
                        'expiry': metadata.get('expiry'),
                        'expired': is_expired,
                        'size_kb': round(size_kb, 2)
                    })
                except Exception as e:
                    logger.warning(f"Failed to read metadata from {meta_file}: {e}")
                    continue
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            return []


# Singleton instances for different namespaces
_cache_instances = {}


def get_cache(namespace: str, expiry_hours: int = 168, **kwargs) -> CacheManager:
    """
    Get or create a cache instance for a namespace
    
    Args:
        namespace: Cache namespace
        expiry_hours: Cache expiration time in hours
        **kwargs: Additional CacheManager arguments
        
    Returns:
        CacheManager instance
    """
    cache_key = f"{namespace}_{expiry_hours}"
    
    if cache_key not in _cache_instances:
        _cache_instances[cache_key] = CacheManager(
            namespace=namespace,
            expiry_hours=expiry_hours,
            **kwargs
        )
    
    return _cache_instances[cache_key]


# Pre-configured cache instances for common use cases (3 directories to match UI tabs)
stock_cache = get_cache('Stock', expiry_hours=168)  # 1 week - Stock tab data
macro_cache = get_cache('Macro', expiry_hours=24)  # 1 day - Macro/Economy tab data
ai_cache = get_cache('AI', expiry_hours=720)  # 30 days - AI tab data
