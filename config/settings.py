# config/settings.py
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json

@dataclass
class AWSConfig:
    """Configurazione centralizzata per l'audit AWS"""
    regions: List[str] = field(default_factory=lambda: ["us-east-1"])
    profile: Optional[str] = None
    max_workers: int = 10
    cache_ttl: int = 3600  # 1 ora
    output_formats: List[str] = field(default_factory=lambda: ["json", "md"])
    
    # Configurazioni per servizi specifici
    services: Dict[str, bool] = field(default_factory=lambda: {
        "ec2": True,
        "eni": True, 
        "sg": True,
        "vpc": True,
        "subnet": True,
        "igw": True,
        "route_table": True,
        "s3": True,
        "iam": True,
        "rds": False,  # Opzionale
        "lambda": False,  # Opzionale
        "elb": False,  # Opzionale
    })
    
    # Configurazioni audit
    audit_rules: Dict[str, Any] = field(default_factory=lambda: {
        "sg_open_ports": [22, 3389, 3306, 5432],  # Porte sensibili
        "sg_allow_all_cidr": True,  # Check 0.0.0.0/0
        "s3_public_access": True,
        "iam_unused_roles": True,
        "iam_old_access_keys": 90,  # giorni
        "ec2_public_ips": True,
        "vpc_default_usage": True,
    })
    
    # Configurazioni notifiche
    notifications: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False,
        "slack_webhook": None,
        "email_smtp": None,
        "critical_only": True,
    })

    def __post_init__(self):
        """Carica configurazione da environment variables se disponibili"""
        # Regioni
        if env_regions := os.getenv("AWS_AUDIT_REGIONS"):
            self.regions = env_regions.split(",")
        
        # Profilo AWS
        if env_profile := os.getenv("AWS_PROFILE"):
            self.profile = env_profile
            
        # Workers per parallelizzazione
        if env_workers := os.getenv("AWS_AUDIT_MAX_WORKERS"):
            self.max_workers = int(env_workers)
            
        # TTL cache
        if env_ttl := os.getenv("AWS_AUDIT_CACHE_TTL"):
            self.cache_ttl = int(env_ttl)

    @classmethod
    def from_file(cls, config_path: str = "config.json") -> "AWSConfig":
        """Carica configurazione da file JSON"""
        if os.path.exists(config_path):
            with open(config_path) as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save_to_file(self, config_path: str = "config.json"):
        """Salva configurazione su file JSON"""
        with open(config_path, "w") as f:
            # Converte dataclass in dict escludendo i campi None
            config_dict = {
                k: v for k, v in self.__dict__.items() 
                if v is not None
            }
            json.dump(config_dict, f, indent=2)
    
    def get_active_regions(self) -> List[str]:
        """Ritorna le regioni attive per l'audit"""
        return self.regions
    
    def get_active_services(self) -> List[str]:
        """Ritorna i servizi attivi per l'audit"""
        return [service for service, enabled in self.services.items() if enabled]
    
    def is_service_enabled(self, service: str) -> bool:
        """Verifica se un servizio è abilitato"""
        return self.services.get(service, False)
    