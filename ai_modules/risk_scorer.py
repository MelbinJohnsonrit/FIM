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
