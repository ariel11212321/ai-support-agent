"""
AI Support Agent - Question Classification Engine
Advanced classification using keywords, patterns, and contextual analysis
"""

import re
import time
from typing import Dict, List, Tuple, Set
from collections import defaultdict

from models import UserQuestion, ClassificationResult, SupportCategory
from config import Keywords, Patterns, Scoring, Config


class QuestionClassifier:
    """
    Advanced question classifier using multiple techniques:
    - Keyword matching with weighted scores
    - Regex pattern detection
    - Context analysis and urgency detection
    - Confidence calculation based on feature separation
    """
    
    def __init__(self):
        """Initialize the classifier with keyword sets and patterns"""
        self.billing_keywords = Keywords.BILLING_KEYWORDS
        self.technical_keywords = Keywords.TECHNICAL_KEYWORDS
        self.general_keywords = Keywords.GENERAL_KEYWORDS
        self.urgency_keywords = Keywords.URGENCY_KEYWORDS
        
        # Compile regex patterns for performance
        self.money_pattern = re.compile(Patterns.MONEY_PATTERN, re.IGNORECASE)
        self.error_pattern = re.compile(Patterns.ERROR_CODE_PATTERN, re.IGNORECASE)
        self.http_pattern = re.compile(Patterns.HTTP_STATUS_PATTERN)
        self.connection_pattern = re.compile(Patterns.CONNECTION_PATTERN, re.IGNORECASE)
        self.login_pattern = re.compile(Patterns.LOGIN_PATTERN, re.IGNORECASE)
        
        # Performance tracking
        self.classification_count = 0
        self.total_processing_time = 0.0
    
    def classify(self, question: UserQuestion, worker_id: int = None) -> ClassificationResult:
        """
        Classify a user question into billing, technical, or general category
        
        Args:
            question: UserQuestion object containing the text to classify
            worker_id: Optional worker ID for tracking
            
        Returns:
            ClassificationResult with category, confidence, and reasoning
        """
        start_time = time.perf_counter()
        
        try:
            # Preprocess text
            text = self._preprocess_text(question.text)
            
            # Extract features
            features = self._extract_features(text)
            
            # Calculate scores for each category
            scores = self._calculate_category_scores(text, features)
            
            # Determine best category
            category, confidence = self._determine_category(scores, features)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(category, scores, features)
            
            # Calculate processing time
            processing_time = (time.perf_counter() - start_time) * 1000
            
            # Update performance tracking
            self._update_performance_tracking(processing_time)
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                processing_time_ms=processing_time,
                features_detected=features,
                worker_id=worker_id
            )
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            
            # Return default classification on error
            return ClassificationResult(
                category=SupportCategory.GENERAL,
                confidence=Config.DEFAULT_CONFIDENCE,
                reasoning=f"Classification error: {str(e)}",
                processing_time_ms=processing_time,
                features_detected=[],
                worker_id=worker_id
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize input text"""
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _extract_features(self, text: str) -> List[str]:
        """Extract relevant features from the text"""
        features = []
        
        # Check for money mentions
        if self.money_pattern.search(text):
            features.append("money_amount")
        
        # Check for error codes
        if self.error_pattern.search(text):
            features.append("error_code")
        
        # Check for HTTP status codes
        if self.http_pattern.search(text):
            features.append("http_error")
        
        # Check for connection issues
        if self.connection_pattern.search(text):
            features.append("connection_issue")
        
        # Check for login problems
        if self.login_pattern.search(text):
            features.append("login_issue")
        
        # Check for urgency indicators
        urgency_matches = sum(1 for keyword in self.urgency_keywords if keyword in text)
        if urgency_matches > 0:
            features.append("urgency")
        
        # Check for question words
        question_words = ['how', 'what', 'when', 'where', 'why', 'which']
        if any(word in text for word in question_words):
            features.append("question_word")
        
        return features
    
    def _calculate_category_scores(self, text: str, features: List[str]) -> Dict[str, float]:
        """Calculate weighted scores for each category"""
        scores = defaultdict(float)
        
        # Keyword matching scores
        billing_score = self._calculate_keyword_score(text, self.billing_keywords)
        technical_score = self._calculate_keyword_score(text, self.technical_keywords)
        general_score = self._calculate_keyword_score(text, self.general_keywords)
        
        # Apply base scores
        scores['billing'] = billing_score * Scoring.BILLING_WEIGHT
        scores['technical'] = technical_score * Scoring.TECHNICAL_WEIGHT
        scores['general'] = general_score * Scoring.GENERAL_WEIGHT
        
        # Apply feature bonuses
        scores = self._apply_feature_bonuses(scores, features)
        
        # Apply pattern bonuses
        scores = self._apply_pattern_bonuses(scores, text)
        
        return dict(scores)
    
    def _calculate_keyword_score(self, text: str, keywords: Set[str]) -> float:
        """Calculate score based on keyword matches"""
        matches = sum(1 for keyword in keywords if keyword in text)
        return matches * Scoring.KEYWORD_BASE_SCORE
    
    def _apply_feature_bonuses(self, scores: Dict[str, float], features: List[str]) -> Dict[str, float]:
        """Apply bonuses based on detected features"""
        feature_bonuses = {
            'money_amount': {'billing': 4.0},
            'error_code': {'technical': 4.0},
            'http_error': {'technical': 5.0},
            'connection_issue': {'technical': 3.0},
            'login_issue': {'technical': 3.0},
            'urgency': {'technical': 2.0, 'billing': 1.0},
            'question_word': {'general': 1.0}
        }
        
        for feature in features:
            if feature in feature_bonuses:
                for category, bonus in feature_bonuses[feature].items():
                    scores[category] += bonus
        
        return scores
    
    def _apply_pattern_bonuses(self, scores: Dict[str, float], text: str) -> Dict[str, float]:
        """Apply bonuses based on regex pattern matches"""
        # Billing patterns
        billing_patterns = [
            (r'cancel.*subscription', 3.0),
            (r'payment.*fail', 4.0),
            (r'refund.*request', 3.0),
            (r'billing.*issue', 3.0),
            (r'charge.*twice', 4.0)
        ]
        
        for pattern, bonus in billing_patterns:
            if re.search(pattern, text):
                scores['billing'] += bonus
        
        # Technical patterns
        technical_patterns = [
            (r'server.*down', 5.0),
            (r'not.*work', 3.0),
            (r'broken|fix|repair', 3.0),
            (r'database.*error', 4.0),
            (r'api.*fail', 4.0)
        ]
        
        for pattern, bonus in technical_patterns:
            if re.search(pattern, text):
                scores['technical'] += bonus
        
        # General patterns
        general_patterns = [
            (r'how.*work', 2.0),
            (r'what.*is', 2.0),
            (r'documentation|tutorial|guide', 3.0)
        ]
        
        for pattern, bonus in general_patterns:
            if re.search(pattern, text):
                scores['general'] += bonus
        
        return scores
    
    def _determine_category(self, scores: Dict[str, float], features: List[str]) -> Tuple[SupportCategory, float]:
        """Determine the best category and calculate confidence"""
        # Find category with highest score
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]
        
        # Calculate confidence based on score separation
        sorted_scores = sorted(scores.values(), reverse=True)
        
        if len(sorted_scores) > 1 and sorted_scores[0] > 0:
            # Confidence based on margin between top two scores
            score_margin = sorted_scores[0] - sorted_scores[1]
            total_score = sum(scores.values())
            
            if total_score > 0:
                confidence = min(0.95, max(0.3, sorted_scores[0] / total_score))
                
                # Boost confidence for clear indicators
                if len(features) >= Scoring.MIN_FEATURES_FOR_HIGH_CONFIDENCE:
                    confidence = min(0.95, confidence + 0.1)
                
                # Boost confidence for high margin
                if score_margin >= 3.0:
                    confidence = min(0.95, confidence + 0.05)
            else:
                confidence = Config.DEFAULT_CONFIDENCE
        else:
            confidence = Config.DEFAULT_CONFIDENCE if max_score == 0 else min(0.95, max_score / 10)
        
        # Apply confidence smoothing
        confidence = max(Config.MIN_CONFIDENCE_THRESHOLD, 
                        confidence - Scoring.CONFIDENCE_SMOOTHING)
        
        # Convert string category to enum
        category_enum = SupportCategory(max_category)
        
        return category_enum, confidence
    
    def _generate_reasoning(self, category: SupportCategory, scores: Dict[str, float], 
                          features: List[str]) -> str:
        """Generate human-readable reasoning for the classification"""
        category_name = category.value.title()
        category_score = scores[category.value]
        
        reasoning_parts = [
            f"Classified as {category_name.lower()} (score: {category_score:.1f})"
        ]
        
        # Add feature-based reasoning
        if features:
            feature_descriptions = {
                'money_amount': 'financial amounts detected',
                'error_code': 'error codes found',
                'http_error': 'HTTP status errors detected',
                'connection_issue': 'connection problems identified',
                'login_issue': 'login difficulties detected',
                'urgency': 'urgency indicators present',
                'question_word': 'informational question detected'
            }
            
            relevant_features = [feature_descriptions.get(f, f) for f in features]
            if relevant_features:
                reasoning_parts.append(f"Features: {', '.join(relevant_features)}")
        
        # Add score comparison
        other_scores = {k: v for k, v in scores.items() if k != category.value}
        if other_scores:
            max_other = max(other_scores.values())
            margin = category_score - max_other
            if margin > 2.0:
                reasoning_parts.append(f"Clear margin over other categories (+{margin:.1f})")
        
        return "; ".join(reasoning_parts)
    
    def _update_performance_tracking(self, processing_time: float) -> None:
        """Update internal performance tracking"""
        self.classification_count += 1
        self.total_processing_time += processing_time
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if self.classification_count == 0:
            return {
                'total_classifications': 0,
                'average_processing_time_ms': 0.0,
                'total_processing_time_ms': 0.0
            }
        
        return {
            'total_classifications': self.classification_count,
            'average_processing_time_ms': self.total_processing_time / self.classification_count,
            'total_processing_time_ms': self.total_processing_time
        }
    
    def reset_performance_stats(self) -> None:
        """Reset performance tracking counters"""
        self.classification_count = 0
        self.total_processing_time = 0.0


class ClassificationValidator:
    """Utility class for validating classification results"""
    
    @staticmethod
    def is_high_confidence(result: ClassificationResult) -> bool:
        """Check if classification has high confidence"""
        return result.confidence >= Scoring.CONFIDENCE_SMOOTHING
    
    @staticmethod
    def should_escalate(result: ClassificationResult) -> bool:
        """Determine if classification should be escalated"""
        # Escalate if confidence is too low
        if result.confidence < Config.MIN_CONFIDENCE_THRESHOLD:
            return True
        
        # Escalate if urgent features detected
        urgent_features = {'urgency', 'error_code', 'http_error', 'connection_issue'}
        if any(feature in result.features_detected for feature in urgent_features):
            return True
        
        return False
    
    @staticmethod
    def get_quality_score(result: ClassificationResult) -> float:
        """Calculate overall quality score for classification"""
        # Base score from confidence
        quality = result.confidence
        
        # Bonus for fast processing
        if result.processing_time_ms < 50:
            quality += 0.1
        
        # Bonus for multiple features
        if len(result.features_detected) >= 2:
            quality += 0.05
        
        # Cap at 1.0
        return min(1.0, quality)