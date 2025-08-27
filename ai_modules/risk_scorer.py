import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class AIRiskScorer:
    """
    \"\"\"
    AI-powered risk scoring system for File Integrity Monitoring
    Uses machine learning algorithms to assess risk levels of file changes
    \"\"\"
    """
    
    def __init__(self, config_path='config/settings.json'):
        self.config = self.load_config(config_path)
        self.model = None
        self.scaler = StandardScaler()
        self.risk_threshold = 0.7
        self.model_path = 'models/fim_risk_model.pkl'
        self.scaler_path = 'models/fim_scaler.pkl'
        self.feature_history = []
        self.logger = self.setup_logging()
        
        # Risk scoring weights
        self.risk_weights = {
            'file_type_risk': 0.25,
            'location_risk': 0.20,
            'time_risk': 0.15,
            'change_magnitude': 0.20,
            'user_behavior': 0.20
        }
        
        # Critical file patterns and risk levels
        self.critical_patterns = {
            'system_files': {
                'patterns': ['/etc/', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/'],
                'risk_score': 0.9
            },
            'config_files': {
                'patterns': ['.conf', '.cfg', '.ini', 'config'],
                'risk_score': 0.8
            },
            'executable_files': {
                'patterns': ['.exe', '.bat', '.sh', '.ps1', '.py'],
                'risk_score': 0.7
            },
            'data_files': {
                'patterns': ['.db', '.sql', '.csv', '.json'],
                'risk_score': 0.6
            },
            'log_files': {
                'patterns': ['.log', '.txt'],
                'risk_score': 0.3
            }
        }
        
    def load_config(self, path: str) -> Dict:
        #\"\"\"Load configuration from JSON file\"\"\"
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def setup_logging(self) -> logging.Logger:
        #\"\"\"Setup logging for the AI risk scorer\"\"\"
        logger = logging.getLogger('AIRiskScorer')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('logs/ai_risk_scorer.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def extract_features(self, file_path: str, change_type: str, metadata: Dict) -> Dict:
        """
        \"\"\"
        Extract features for AI risk scoring
        
        Args:
            file_path: Path to the file
            change_type: Type of change (modified, new, deleted)
            metadata: File metadata including hash, size, timestamps
            
        Returns:
            Dictionary of extracted features
        \"\"\"
        """
        now = datetime.now()
        
        features = {
            # File type and location features
            'file_extension_risk': self.get_file_extension_risk(file_path),
            'location_risk': self.get_location_risk(file_path),
            'is_hidden_file': 1 if os.path.basename(file_path).startswith('.') else 0,
            'is_system_path': self.is_system_path(file_path),
            
            # Time-based features
            'hour_of_change': now.hour,
            'day_of_week': now.weekday(),
            'is_weekend': 1 if now.weekday() >= 5 else 0,
            'is_business_hours': 1 if 9 <= now.hour <= 17 else 0,
            
            # Change characteristics
            'change_type_modified': 1 if change_type == 'modified' else 0,
            'change_type_new': 1 if change_type == 'new' else 0,
            'change_type_deleted': 1 if change_type == 'deleted' else 0,
            
            # File size features
            'file_size': metadata.get('size', 0),
            'size_category': self.categorize_file_size(metadata.get('size', 0)),
            
            # Historical features
            'change_frequency': self.get_change_frequency(file_path),
            'time_since_last_change': self.get_time_since_last_change(file_path),
            
            # Permission features
            'permission_risk': self.get_permission_risk(metadata.get('permissions', '644'))
        }
        
        return features
    def get_file_extension_risk(self, file_path: str) -> float:
        #\"\"\"Calculate risk based on file extension\"\"\"
        ext = os.path.splitext(file_path)[1].lower()
        
        high_risk_extensions = ['.exe', '.bat', '.sh', '.ps1', '.dll', '.so']
        medium_risk_extensions = ['.py', '.js', '.php', '.pl', '.rb']
        config_extensions = ['.conf', '.cfg', '.ini', '.yml', '.yaml', '.json']
        
        if ext in high_risk_extensions:
            return 0.9
        elif ext in medium_risk_extensions:
            return 0.7
        elif ext in config_extensions:
            return 0.6
        else:
            return 0.3
    
    def get_location_risk(self, file_path: str) -> float:
        #\"\"\"Calculate risk based on file location\"\"\"
        path_lower = file_path.lower()
        
        for category, info in self.critical_patterns.items():
            for pattern in info['patterns']:
                if pattern in path_lower:
                    return info['risk_score']
        
        return 0.3  # Default low risk
    
    def is_system_path(self, file_path: str) -> int:
        #\"\"\"Check if file is in a system path\"\"\"
        system_paths = ['/etc/', '/bin/', '/sbin/', '/usr/', '/var/', '/sys/', '/proc/']
        return 1 if any(path in file_path for path in system_paths) else 0
    
    def categorize_file_size(self, size: int) -> int:
        #\"\"\"Categorize file size for risk assessment\"\"\"
        if size > 100 * 1024 * 1024:  # > 100MB
            return 4
        elif size > 10 * 1024 * 1024:  # > 10MB
            return 3
        elif size > 1024 * 1024:  # > 1MB
            return 2
        elif size > 1024:  # > 1KB
            return 1
        else:
            return 0
    
    def get_change_frequency(self, file_path: str) -> float:
        #\"\"\"Calculate how frequently this file changes\"\"\"
        # This would typically query historical data
        # For now, return a default value
        return 0.1
    
    def get_time_since_last_change(self, file_path: str) -> float:
        #\"\"\"Calculate time since last change in hours\"\"\"
        # This would typically query historical data
        # For now, return a default value
        return 24.0
    
    def get_permission_risk(self, permissions: str) -> float:
        #\"\"\"Calculate risk based on file permissions\"\"\"
        if permissions.endswith('777') or permissions.endswith('666'):
            return 0.9  # World writable is high risk
        elif permissions.endswith('755') or permissions.endswith('644'):
            return 0.3  # Standard permissions
        else:
            return 0.5  # Medium risk for other permissions
    
    def calculate_rule_based_risk(self, features: Dict) -> float:
        """
        \"\"\"
        Calculate risk score using rule-based approach
        
        Args:
            features: Extracted features dictionary
            
        Returns:
            Risk score between 0 and 1
        \"\"\"
        """
        risk_score = 0.0
        
        # File type and location risk
        risk_score += features['file_extension_risk'] * self.risk_weights['file_type_risk']
        risk_score += features['location_risk'] * self.risk_weights['location_risk']
        
        # Time-based risk
        time_risk = 0.3  # Default
        if not features['is_business_hours']:
            time_risk += 0.4
        if features['is_weekend']:
            time_risk += 0.3
        risk_score += min(time_risk, 1.0) * self.risk_weights['time_risk']
        
        # Change magnitude risk
        change_risk = 0.5  # Default
        if features['change_type_deleted']:
            change_risk = 0.8
        elif features['change_type_new'] and features['is_system_path']:
            change_risk = 0.9
        risk_score += change_risk * self.risk_weights['change_magnitude']
        
        # User behavior risk (simplified)
        behavior_risk = 0.4
        if features['change_frequency'] > 0.5:
            behavior_risk = 0.2  # Frequent changes are less suspicious
        risk_score += behavior_risk * self.risk_weights['user_behavior']
        
        return min(risk_score, 1.0)
