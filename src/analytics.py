"""
AI Support Agent - Advanced Analytics Engine
Comprehensive analytics, performance tracking, and insights generation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import asdict

from models import (
    UserQuestion, ClassificationResult, SupportResponse, 
    AnalyticsData, SupportCategory, Priority
)
from config import Config


class AnalyticsEngine:
    """
    Comprehensive analytics engine for tracking performance, usage patterns,
    and generating actionable insights
    """
    
    def __init__(self):
        """Initialize analytics engine"""
        self.start_time = datetime.now()
        
        # Core analytics data
        self.analytics_data = AnalyticsData()
        
        # Detailed tracking
        self.session_data: Dict[str, List] = defaultdict(list)
        self.hourly_stats: Dict[int, Dict] = defaultdict(lambda: {
            'questions': 0,
            'categories': defaultdict(int),
            'avg_confidence': 0.0,
            'avg_processing_time': 0.0
        })
        
        # Performance tracking
        self.performance_history: List[Dict] = []
        self.error_log: List[Dict] = []
        
        # User behavior tracking
        self.user_patterns: Dict[str, Dict] = defaultdict(lambda: {
            'total_questions': 0,
            'categories': defaultdict(int),
            'avg_confidence': 0.0,
            'last_seen': None,
            'session_count': 0
        })
        
        # Classification accuracy tracking
        self.classification_feedback: List[Dict] = []
        self.confidence_buckets = {
            'low': {'range': (0.0, 0.5), 'count': 0, 'correct': 0},
            'medium': {'range': (0.5, 0.8), 'count': 0, 'correct': 0},
            'high': {'range': (0.8, 1.0), 'count': 0, 'correct': 0}
        }
        
        # Trending and patterns
        self.trending_keywords: Counter = Counter()
        self.category_trends: Dict[str, List] = defaultdict(list)
        
    def record_interaction(self, question: UserQuestion, classification: ClassificationResult, 
                          response: SupportResponse) -> None:
        """
        Record a complete question-response interaction
        
        Args:
            question: The user question
            classification: Classification result
            response: Generated response
        """
        timestamp = datetime.now()
        
        # Update core analytics
        self.analytics_data.update_metrics(classification, response)
        
        # Record session data
        session_id = question.session_id or 'anonymous'
        self.session_data[session_id].append({
            'timestamp': timestamp.isoformat(),
            'question': question.text,
            'category': classification.category.value,
            'confidence': classification.confidence,
            'processing_time': classification.processing_time_ms,
            'escalation_needed': response.escalation_needed,
            'priority': response.priority.value
        })
        
        # Update hourly statistics
        hour = timestamp.hour
        hourly_stat = self.hourly_stats[hour]
        hourly_stat['questions'] += 1
        hourly_stat['categories'][classification.category.value] += 1
        
        # Update running averages for the hour
        current_count = hourly_stat['questions']
        hourly_stat['avg_confidence'] = (
            (hourly_stat['avg_confidence'] * (current_count - 1) + classification.confidence) 
            / current_count
        )
        hourly_stat['avg_processing_time'] = (
            (hourly_stat['avg_processing_time'] * (current_count - 1) + classification.processing_time_ms) 
            / current_count
        )
        
        # Update user patterns
        user_id = question.user_id
        user_pattern = self.user_patterns[user_id]
        user_pattern['total_questions'] += 1
        user_pattern['categories'][classification.category.value] += 1
        user_pattern['last_seen'] = timestamp.isoformat()
        
        # Update user's average confidence
        total_q = user_pattern['total_questions']
        user_pattern['avg_confidence'] = (
            (user_pattern['avg_confidence'] * (total_q - 1) + classification.confidence) 
            / total_q
        )
        
        # Track trending keywords
        words = question.text.lower().split()
        meaningful_words = [word for word in words if len(word) > 3]
        self.trending_keywords.update(meaningful_words)
        
        # Track category trends (for time series analysis)
        today = timestamp.date().isoformat()
        self.category_trends[classification.category.value].append({
            'date': today,
            'hour': hour,
            'confidence': classification.confidence
        })
        
        # Track confidence buckets for accuracy analysis
        for bucket_name, bucket_data in self.confidence_buckets.items():
            min_conf, max_conf = bucket_data['range']
            if min_conf <= classification.confidence < max_conf:
                bucket_data['count'] += 1
                break
        
        # Record performance snapshot
        if len(self.performance_history) == 0 or len(self.performance_history) % 10 == 0:
            self._record_performance_snapshot()
    
    def record_error(self, error_type: str, error_message: str, context: Dict = None) -> None:
        """Record an error for analytics"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': error_message,
            'context': context or {}
        }
        
        self.error_log.append(error_entry)
        
        # Keep only recent errors
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-500:]
    
    def record_feedback(self, question_text: str, predicted_category: str, 
                       actual_category: str, was_correct: bool) -> None:
        """
        Record classification feedback for accuracy tracking
        
        Args:
            question_text: Original question
            predicted_category: What the classifier predicted
            actual_category: What it should have been
            was_correct: Whether the classification was correct
        """
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': question_text,
            'predicted': predicted_category,
            'actual': actual_category,
            'correct': was_correct
        }
        
        self.classification_feedback.append(feedback_entry)
        
        # Update confidence bucket accuracy
        # Note: This would need the original confidence score
        # For now, we'll track overall accuracy
        
        # Keep only recent feedback
        if len(self.classification_feedback) > 500:
            self.classification_feedback = self.classification_feedback[-250:]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_time = datetime.now()
        uptime = current_time - self.start_time
        
        # Today's statistics
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_sessions = []
        
        for session_interactions in self.session_data.values():
            today_interactions = [
                interaction for interaction in session_interactions
                if datetime.fromisoformat(interaction['timestamp']) >= today_start
            ]
            if today_interactions:
                today_sessions.extend(today_interactions)
        
        # Category distribution
        category_dist = dict(self.analytics_data.category_counts)
        
        # Peak hours analysis
        peak_hour = max(self.hourly_stats.items(), key=lambda x: x[1]['questions']) if self.hourly_stats else (0, {'questions': 0})
        
        return {
            'overview': {
                'total_questions': self.analytics_data.total_questions,
                'uptime_hours': uptime.total_seconds() / 3600,
                'average_confidence': self.analytics_data.average_confidence,
                'average_processing_time_ms': self.analytics_data.average_processing_time,
                'accuracy_rate': self.analytics_data.accuracy_rate,
                'cache_hit_rate': self.analytics_data.cache_hit_rate
            },
            'today': {
                'questions_today': len(today_sessions),
                'unique_users': len(set(interaction.get('user_id', 'anonymous') for interaction in today_sessions)),
                'peak_hour': f"{peak_hour[0]:02d}:00 ({peak_hour[1]['questions']} questions)"
            },
            'categories': {
                'distribution': category_dist,
                'top_category': self.analytics_data.get_top_category()
            },
            'performance': {
                'avg_response_time': self.analytics_data.average_processing_time,
                'total_errors': len(self.error_log),
                'recent_errors': len([e for e in self.error_log if 
                                   datetime.fromisoformat(e['timestamp']) > current_time - timedelta(hours=1)])
            },
            'trends': {
                'trending_keywords': dict(self.trending_keywords.most_common(10)),
                'hourly_pattern': self._get_hourly_pattern(),
                'category_trends': self._get_category_trends()
            }
        }
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Generate performance insights and recommendations"""
        insights = {
            'classification_accuracy': self._analyze_classification_accuracy(),
            'performance_trends': self._analyze_performance_trends(),
            'user_behavior': self._analyze_user_behavior(),
            'system_health': self._analyze_system_health(),
            'recommendations': self._generate_recommendations()
        }
        
        return insights
    
    def get_category_analysis(self, category: SupportCategory) -> Dict[str, Any]:
        """Get detailed analysis for a specific category"""
        category_name = category.value
        
        # Filter data for this category
        category_sessions = []
        for session_interactions in self.session_data.values():
            category_interactions = [
                interaction for interaction in session_interactions
                if interaction['category'] == category_name
            ]
            category_sessions.extend(category_interactions)
        
        if not category_sessions:
            return {'error': f'No data available for category: {category_name}'}
        
        # Calculate statistics
        confidences = [interaction['confidence'] for interaction in category_sessions]
        processing_times = [interaction['processing_time'] for interaction in category_sessions]
        escalation_rate = sum(1 for interaction in category_sessions if interaction['escalation_needed']) / len(category_sessions)
        
        # Priority distribution
        priorities = [interaction['priority'] for interaction in category_sessions]
        priority_dist = dict(Counter(priorities))
        
        # Time analysis
        timestamps = [datetime.fromisoformat(interaction['timestamp']) for interaction in category_sessions]
        hourly_dist = Counter(ts.hour for ts in timestamps)
        
        return {
            'category': category_name,
            'total_questions': len(category_sessions),
            'average_confidence': sum(confidences) / len(confidences),
            'confidence_range': {'min': min(confidences), 'max': max(confidences)},
            'average_processing_time': sum(processing_times) / len(processing_times),
            'escalation_rate': escalation_rate * 100,
            'priority_distribution': priority_dist,
            'hourly_distribution': dict(hourly_dist),
            'peak_hours': [hour for hour, count in hourly_dist.most_common(3)],
            'recent_questions': [
                interaction['question'] for interaction in 
                sorted(category_sessions, key=lambda x: x['timestamp'], reverse=True)[:5]
            ]
        }
    
    def get_user_insights(self, user_id: str = None) -> Dict[str, Any]:
        """Get user behavior insights"""
        if user_id:
            # Specific user analysis
            if user_id not in self.user_patterns:
                return {'error': f'No data for user: {user_id}'}
            
            pattern = self.user_patterns[user_id]
            sessions = self.session_data.get(user_id, [])
            
            return {
                'user_id': user_id,
                'total_questions': pattern['total_questions'],
                'category_preferences': dict(pattern['categories']),
                'average_confidence': pattern['avg_confidence'],
                'last_seen': pattern['last_seen'],
                'session_count': len(sessions),
                'question_history': sessions[-10:]  # Last 10 questions
            }
        else:
            # Overall user behavior analysis
            total_users = len(self.user_patterns)
            active_users_24h = sum(1 for pattern in self.user_patterns.values() 
                                 if pattern['last_seen'] and 
                                 datetime.fromisoformat(pattern['last_seen']) > datetime.now() - timedelta(days=1))
            
            # User engagement levels
            engagement_levels = {
                'high': sum(1 for p in self.user_patterns.values() if p['total_questions'] >= 10),
                'medium': sum(1 for p in self.user_patterns.values() if 3 <= p['total_questions'] < 10),
                'low': sum(1 for p in self.user_patterns.values() if p['total_questions'] < 3)
            }
            
            return {
                'total_users': total_users,
                'active_users_24h': active_users_24h,
                'engagement_levels': engagement_levels,
                'average_questions_per_user': (
                    sum(p['total_questions'] for p in self.user_patterns.values()) / total_users
                    if total_users > 0 else 0
                ),
                'top_users': [
                    {'user_id': uid, 'questions': pattern['total_questions']}
                    for uid, pattern in sorted(
                        self.user_patterns.items(),
                        key=lambda x: x[1]['total_questions'],
                        reverse=True
                    )[:10]
                ]
            }
    
    def _record_performance_snapshot(self) -> None:
        """Record a performance snapshot"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'total_questions': self.analytics_data.total_questions,
            'average_confidence': self.analytics_data.average_confidence,
            'average_processing_time': self.analytics_data.average_processing_time,
            'error_rate': len(self.error_log) / max(self.analytics_data.total_questions, 1),
            'category_distribution': dict(self.analytics_data.category_counts)
        }
        
        self.performance_history.append(snapshot)
        
        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]
    
    def _get_hourly_pattern(self) -> Dict[int, int]:
        """Get question count by hour of day"""
        return {hour: stats['questions'] for hour, stats in self.hourly_stats.items()}
    
    def _get_category_trends(self) -> Dict[str, List]:
        """Get category trends over time"""
        trends = {}
        
        for category, trend_data in self.category_trends.items():
            # Group by date
            daily_counts = defaultdict(int)
            for entry in trend_data:
                daily_counts[entry['date']] += 1
            
            trends[category] = [
                {'date': date, 'count': count}
                for date, count in sorted(daily_counts.items())
            ]
        
        return trends
    
    def _analyze_classification_accuracy(self) -> Dict[str, Any]:
        """Analyze classification accuracy"""
        if not self.classification_feedback:
            return {'message': 'No feedback data available'}
        
        total_feedback = len(self.classification_feedback)
        correct_predictions = sum(1 for f in self.classification_feedback if f['correct'])
        accuracy = correct_predictions / total_feedback * 100
        
        # Category-specific accuracy
        category_accuracy = defaultdict(lambda: {'correct': 0, 'total': 0})
        for feedback in self.classification_feedback:
            category = feedback['predicted']
            category_accuracy[category]['total'] += 1
            if feedback['correct']:
                category_accuracy[category]['correct'] += 1
        
        category_rates = {
            cat: (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            for cat, stats in category_accuracy.items()
        }
        
        return {
            'overall_accuracy': accuracy,
            'total_feedback_samples': total_feedback,
            'category_accuracy': category_rates,
            'confidence_bucket_accuracy': {
                bucket: (data['correct'] / data['count'] * 100) if data['count'] > 0 else 0
                for bucket, data in self.confidence_buckets.items()
            }
        }
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.performance_history) < 2:
            return {'message': 'Insufficient data for trend analysis'}
        
        recent = self.performance_history[-10:]  # Last 10 snapshots
        
        # Calculate trends
        response_times = [snapshot['average_processing_time'] for snapshot in recent]
        confidences = [snapshot['average_confidence'] for snapshot in recent]
        
        response_time_trend = 'improving' if response_times[-1] < response_times[0] else 'degrading'
        confidence_trend = 'improving' if confidences[-1] > confidences[0] else 'degrading'
        
        return {
            'response_time_trend': response_time_trend,
            'confidence_trend': confidence_trend,
            'current_avg_response_time': response_times[-1] if response_times else 0,
            'current_avg_confidence': confidences[-1] if confidences else 0,
            'performance_stability': self._calculate_stability(response_times)
        }
    
    def _analyze_user_behavior(self) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        # Session length analysis
        session_lengths = []
        for sessions in self.session_data.values():
            if len(sessions) > 1:
                first = datetime.fromisoformat(sessions[0]['timestamp'])
                last = datetime.fromisoformat(sessions[-1]['timestamp'])
                duration = (last - first).total_seconds() / 60  # minutes
                session_lengths.append(duration)
        
        avg_session_length = sum(session_lengths) / len(session_lengths) if session_lengths else 0
        
        # Question complexity analysis
        avg_question_length = []
        for sessions in self.session_data.values():
            for interaction in sessions:
                avg_question_length.append(len(interaction['question'].split()))
        
        avg_words_per_question = sum(avg_question_length) / len(avg_question_length) if avg_question_length else 0
        
        return {
            'average_session_length_minutes': avg_session_length,
            'average_words_per_question': avg_words_per_question,
            'repeat_user_rate': self._calculate_repeat_user_rate(),
            'category_switching_rate': self._calculate_category_switching_rate()
        }
    
    def _analyze_system_health(self) -> Dict[str, Any]:
        """Analyze overall system health"""
        recent_errors = [
            error for error in self.error_log 
            if datetime.fromisoformat(error['timestamp']) > datetime.now() - timedelta(hours=1)
        ]
        
        error_rate = len(recent_errors) / max(self.analytics_data.total_questions, 1) * 100
        
        return {
            'error_rate_percent': error_rate,
            'recent_errors_count': len(recent_errors),
            'system_uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'avg_response_time_ms': self.analytics_data.average_processing_time,
            'health_status': 'healthy' if error_rate < 1 else 'degraded' if error_rate < 5 else 'critical'
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        # Performance recommendations
        if self.analytics_data.average_processing_time > 100:
            recommendations.append("Consider optimizing classification algorithms - response times are above target")
        
        # Accuracy recommendations
        if self.analytics_data.average_confidence < 0.7:
            recommendations.append("Review keyword dictionaries and patterns - confidence scores are low")
        
        # Usage pattern recommendations
        peak_hours = [hour for hour, stats in self.hourly_stats.items() if stats['questions'] > 10]
        if len(peak_hours) < 3:
            recommendations.append("Consider expanding service hours - usage is concentrated in few hours")
        
        # Error rate recommendations
        recent_error_rate = len([e for e in self.error_log 
                               if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=24)]) / 24
        if recent_error_rate > 1:
            recommendations.append("Investigate recent errors - error rate has increased")
        
        # Category distribution recommendations
        category_counts = self.analytics_data.category_counts
        if category_counts:
            max_category = max(category_counts, key=category_counts.get)
            if category_counts[max_category] > sum(category_counts.values()) * 0.7:
                recommendations.append(f"Consider specialized handling for {max_category} category - it dominates traffic")
        
        return recommendations
    
    def _calculate_stability(self, values: List[float]) -> float:
        """Calculate stability score (lower variance = higher stability)"""
        if len(values) < 2:
            return 1.0
        
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        
        # Normalize to 0-1 scale (1 = very stable)
        stability = max(0, 1 - (variance / mean_val if mean_val > 0 else 1))
        return stability
    
    def _calculate_repeat_user_rate(self) -> float:
        """Calculate percentage of users who ask multiple questions"""
        total_users = len(self.user_patterns)
        repeat_users = sum(1 for pattern in self.user_patterns.values() if pattern['total_questions'] > 1)
        
        return (repeat_users / total_users * 100) if total_users > 0 else 0
    
    def _calculate_category_switching_rate(self) -> float:
        """Calculate how often users switch between categories"""
        switches = 0
        total_sessions = 0
        
        for sessions in self.session_data.values():
            if len(sessions) > 1:
                total_sessions += 1
                categories = [interaction['category'] for interaction in sessions]
                
                for i in range(1, len(categories)):
                    if categories[i] != categories[i-1]:
                        switches += 1
        
        return (switches / total_sessions) if total_sessions > 0 else 0