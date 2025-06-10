# utils/cache_manager.py  
import hashlib
import json
import time
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    checksum: str
    region: str
    service: str

class SmartCache:
    """Cache intelligente per i dati AWS con TTL configurabile"""
    
    def __init__(self, cache_dir: str = ".cache", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, service: str, region: str, **kwargs) -> str:
        """Genera chiave cache univoca"""
        key_data = f"{service}:{region}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, service: str, region: str, **kwargs) -> Optional[Any]:
        """Recupera dati dalla cache se validi"""
        cache_key = self._generate_cache_key(service, region, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
                entry = CacheEntry(**cache_data)
            
            # Verifica TTL
            if time.time() - entry.timestamp > self.ttl:
                cache_file.unlink()  # Rimuovi cache scaduta
                return None
            
            return entry.data
            
        except Exception:
            # Cache corrotta, rimuovi
            cache_file.unlink()
            return None
    
    def set(self, service: str, region: str, data: Any, **kwargs):
        """Salva dati in cache"""
        cache_key = self._generate_cache_key(service, region, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            checksum=self._calculate_checksum(data),
            region=region,
            service=service
        )
        
        with open(cache_file, 'w') as f:
            json.dump(entry.__dict__, f, default=str, indent=2)
    
    def _calculate_checksum(self, data: Any) -> str:
        """Calcola checksum dei dati"""
        return hashlib.md5(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()
    
    def clear_cache(self, service: Optional[str] = None):
        """Pulisce cache (opzionalmente per servizio specifico)"""
        for cache_file in self.cache_dir.glob("*.json"):
            if service is None:
                cache_file.unlink()
            else:
                try:
                    with open(cache_file) as f:
                        cache_data = json.load(f)
                    if cache_data.get("service") == service:
                        cache_file.unlink()
                except:
                    pass
    
    def get_cache_stats(self) -> dict:
        """Ritorna statistiche della cache"""
        stats = {"total_files": 0, "total_size": 0, "by_service": {}}
        
        for cache_file in self.cache_dir.glob("*.json"):
            stats["total_files"] += 1
            stats["total_size"] += cache_file.stat().st_size
            
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)
                service = cache_data.get("service", "unknown")
                if service not in stats["by_service"]:
                    stats["by_service"][service] = 0
                stats["by_service"][service] += 1
            except:
                pass
        
        return stats