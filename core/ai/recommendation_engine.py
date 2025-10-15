"""Personalized recommendation engine based on user behavior analysis."""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pandas as pd

from config.database import SessionLocal
from database.models import User, CSVAnalysis, AnalyticsReport, TopTheme, GlobalTheme, ThemeRequest


class RecommendationEngine:
    """Generate personalized recommendations based on user behavior."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_user_behavior_profile(self, user_id: int) -> Dict[str, Any]:
        """Create user behavior profile from historical data."""
        try:
            # Get user's successful themes
            successful_themes = self.db.query(TopTheme).join(CSVAnalysis).filter(
                and_(
                    CSVAnalysis.user_id == user_id,
                    TopTheme.revenue > 0
                )
            ).order_by(desc(TopTheme.revenue)).limit(20).all()
            
            # Get user's theme requests
            theme_requests = self.db.query(ThemeRequest).filter(
                ThemeRequest.user_id == user_id
            ).order_by(desc(ThemeRequest.requested_at)).limit(50).all()
            
            # Analyze user preferences
            theme_preferences = {}
            for theme in successful_themes:
                theme_name = theme.theme_name.lower()
                if theme_name not in theme_preferences:
                    theme_preferences[theme_name] = {
                        'count': 0,
                        'total_revenue': 0,
                        'avg_revenue': 0
                    }
                theme_preferences[theme_name]['count'] += 1
                theme_preferences[theme_name]['total_revenue'] += float(theme.revenue)
                theme_preferences[theme_name]['avg_revenue'] = (
                    theme_preferences[theme_name]['total_revenue'] / 
                    theme_preferences[theme_name]['count']
                )
            
            # Get user activity patterns
            csv_analyses = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).order_by(CSVAnalysis.created_at).all()
            
            # Calculate activity metrics
            total_analyses = len(csv_analyses)
            avg_monthly_analyses = total_analyses / max(1, (datetime.utcnow() - csv_analyses[0].created_at).days / 30) if csv_analyses else 0
            
            # Get user subscription info
            user = self.db.query(User).filter(User.id == user_id).first()
            
            return {
                "user_id": user_id,
                "subscription_type": user.subscription_type if user else "FREE",
                "successful_themes": len(successful_themes),
                "theme_preferences": theme_preferences,
                "total_analyses": total_analyses,
                "avg_monthly_analyses": round(avg_monthly_analyses, 1),
                "theme_requests_count": len(theme_requests),
                "profile_strength": min(100, len(successful_themes) * 5 + total_analyses * 2)
            }
            
        except Exception as e:
            print(f"Error creating user behavior profile: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def get_personalized_themes(self, user_id: int, count: int = 5) -> List[Dict[str, Any]]:
        """Get personalized theme recommendations."""
        try:
            profile = self.get_user_behavior_profile(user_id)
            
            if profile.get("error"):
                return self._get_fallback_themes(count)
            
            # Get user's successful themes
            successful_themes = list(profile["theme_preferences"].keys())
            
            if not successful_themes:
                return self._get_trending_themes(count)
            
            # Find similar themes using TF-IDF
            all_themes = self._get_all_available_themes()
            if not all_themes:
                return self._get_fallback_themes(count)
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            theme_texts = successful_themes + all_themes
            tfidf_matrix = vectorizer.fit_transform(theme_texts)
            
            # Calculate similarity
            user_vectors = tfidf_matrix[:len(successful_themes)]
            available_vectors = tfidf_matrix[len(successful_themes):]
            
            similarities = cosine_similarity(user_vectors, available_vectors)
            avg_similarities = np.mean(similarities, axis=0)
            
            # Get top similar themes
            top_indices = np.argsort(avg_similarities)[::-1][:count * 2]  # Get more for filtering
            
            recommendations = []
            for idx in top_indices:
                if len(recommendations) >= count:
                    break
                
                theme_name = all_themes[idx]
                similarity_score = avg_similarities[idx]
                
                # Skip themes user already has
                if theme_name.lower() not in successful_themes:
                    recommendations.append({
                        "theme": theme_name,
                        "similarity_score": round(similarity_score, 3),
                        "reason": "Похоже на ваши успешные темы",
                        "confidence": "high" if similarity_score > 0.3 else "medium"
                    })
            
            # If not enough recommendations, add trending themes
            if len(recommendations) < count:
                trending = self._get_trending_themes(count - len(recommendations))
                recommendations.extend(trending)
            
            return recommendations[:count]
            
        except Exception as e:
            print(f"Error getting personalized themes: {e}")
            return self._get_fallback_themes(count)
    
    def get_optimal_upload_time(self, user_id: int) -> Dict[str, Any]:
        """Suggest optimal upload time based on user's historical performance."""
        try:
            # Get user's CSV analyses with timestamps
            analyses = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user_id
            ).order_by(CSVAnalysis.created_at).all()
            
            if len(analyses) < 3:
                return {
                    "optimal_day": "any",
                    "optimal_time": "morning",
                    "message": "Недостаточно данных для анализа оптимального времени"
                }
            
            # Analyze performance by day of week
            day_performance = {}
            for analysis in analyses:
                day_of_week = analysis.created_at.strftime('%A')
                if day_of_week not in day_performance:
                    day_performance[day_of_week] = []
                
                # Get report for this analysis
                report = analysis.analytics_report
                if report:
                    day_performance[day_of_week].append(float(report.total_revenue) if report.total_revenue else 0)
            
            # Find best performing day
            best_day = None
            best_avg_revenue = 0
            
            for day, revenues in day_performance.items():
                if revenues:
                    avg_revenue = np.mean(revenues)
                    if avg_revenue > best_avg_revenue:
                        best_avg_revenue = avg_revenue
                        best_day = day
            
            # Convert to Russian
            day_translation = {
                'Monday': 'Понедельник',
                'Tuesday': 'Вторник', 
                'Wednesday': 'Среда',
                'Thursday': 'Четверг',
                'Friday': 'Пятница',
                'Saturday': 'Суббота',
                'Sunday': 'Воскресенье'
            }
            
            optimal_day = day_translation.get(best_day, "любой день")
            
            # Suggest optimal time based on general patterns
            optimal_time = "утро (9-12)"  # Default recommendation
            
            return {
                "optimal_day": optimal_day,
                "optimal_time": optimal_time,
                "best_performance": round(best_avg_revenue, 2),
                "message": f"Лучший день для загрузки: {optimal_day}, время: {optimal_time}"
            }
            
        except Exception as e:
            print(f"Error analyzing optimal upload time: {e}")
            return {
                "optimal_day": "any",
                "optimal_time": "morning",
                "message": f"Ошибка анализа времени: {str(e)}"
            }
    
    def find_similar_users(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Find users with similar behavior patterns."""
        try:
            # Get current user's profile
            current_profile = self.get_user_behavior_profile(user_id)
            
            if current_profile.get("error"):
                return []
            
            # Get all other users with similar subscription type
            subscription_type = current_profile["subscription_type"]
            other_users = self.db.query(User).filter(
                and_(
                    User.id != user_id,
                    User.subscription_type == subscription_type
                )
            ).limit(100).all()
            
            similar_users = []
            
            for user in other_users:
                user_profile = self.get_user_behavior_profile(user.id)
                
                if user_profile.get("error"):
                    continue
                
                # Calculate similarity score
                similarity_score = self._calculate_user_similarity(current_profile, user_profile)
                
                if similarity_score > 0.3:  # Threshold for similarity
                    similar_users.append({
                        "user_id": user.id,
                        "telegram_id": user.telegram_id,
                        "similarity_score": round(similarity_score, 3),
                        "successful_themes": user_profile["successful_themes"],
                        "total_analyses": user_profile["total_analyses"]
                    })
            
            # Sort by similarity and return top results
            similar_users.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_users[:limit]
            
        except Exception as e:
            print(f"Error finding similar users: {e}")
            return []
    
    def get_success_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyze patterns in user's successful themes."""
        try:
            # Get user's top performing themes
            top_themes = self.db.query(TopTheme).join(CSVAnalysis).filter(
                and_(
                    CSVAnalysis.user_id == user_id,
                    TopTheme.revenue > 0
                )
            ).order_by(desc(TopTheme.revenue)).limit(20).all()
            
            if not top_themes:
                return {
                    "patterns": {},
                    "message": "Недостаточно успешных тем для анализа паттернов"
                }
            
            # Analyze theme characteristics
            theme_lengths = [len(theme.theme_name.split()) for theme in top_themes]
            avg_theme_length = np.mean(theme_lengths)
            
            # Analyze revenue distribution
            revenues = [float(theme.revenue) for theme in top_themes]
            avg_revenue = np.mean(revenues)
            revenue_std = np.std(revenues)
            
            # Find common words in successful themes
            all_theme_words = []
            for theme in top_themes:
                words = theme.theme_name.lower().split()
                all_theme_words.extend(words)
            
            # Count word frequency
            word_freq = {}
            for word in all_theme_words:
                if len(word) > 2:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top frequent words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Analyze performance by theme characteristics
            patterns = {
                "avg_theme_length": round(avg_theme_length, 1),
                "avg_revenue": round(avg_revenue, 2),
                "revenue_consistency": round(revenue_std, 2),
                "top_words": [word for word, freq in top_words],
                "total_successful_themes": len(top_themes),
                "best_theme": top_themes[0].theme_name if top_themes else None,
                "best_revenue": float(top_themes[0].revenue) if top_themes else 0
            }
            
            return {
                "patterns": patterns,
                "message": f"Проанализировано {len(top_themes)} успешных тем. Средняя длина: {avg_theme_length:.1f} слов."
            }
            
        except Exception as e:
            print(f"Error analyzing success patterns: {e}")
            return {
                "patterns": {},
                "message": f"Ошибка анализа паттернов: {str(e)}"
            }
    
    def _get_all_available_themes(self) -> List[str]:
        """Get all available themes from global database."""
        try:
            global_themes = self.db.query(GlobalTheme).limit(1000).all()
            return [theme.theme_name for theme in global_themes]
        except Exception as e:
            print(f"Error getting available themes: {e}")
            return []
    
    def _get_trending_themes(self, count: int) -> List[Dict[str, Any]]:
        """Get trending themes as fallback."""
        try:
            trending = self.db.query(GlobalTheme).order_by(desc(GlobalTheme.usage_count)).limit(count).all()
            return [{
                "theme": theme.theme_name,
                "similarity_score": 0.5,
                "reason": "Популярная тема",
                "confidence": "medium"
            } for theme in trending]
        except Exception as e:
            print(f"Error getting trending themes: {e}")
            return []
    
    def _get_fallback_themes(self, count: int) -> List[Dict[str, Any]]:
        """Get fallback themes when no personalization is possible."""
        fallback_themes = [
            "Business", "Technology", "Nature", "Abstract", "Minimalist",
            "Vintage", "Modern", "Creative", "Professional", "Artistic"
        ]
        
        return [{
            "theme": theme,
            "similarity_score": 0.3,
            "reason": "Рекомендуемая тема",
            "confidence": "low"
        } for theme in fallback_themes[:count]]
    
    def _calculate_user_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """Calculate similarity between two user profiles."""
        try:
            # Compare theme preferences
            themes1 = set(profile1["theme_preferences"].keys())
            themes2 = set(profile2["theme_preferences"].keys())
            
            if not themes1 or not themes2:
                return 0.0
            
            # Jaccard similarity for themes
            intersection = len(themes1.intersection(themes2))
            union = len(themes1.union(themes2))
            theme_similarity = intersection / union if union > 0 else 0
            
            # Compare activity levels
            activity1 = profile1["total_analyses"]
            activity2 = profile2["total_analyses"]
            activity_similarity = 1 - abs(activity1 - activity2) / max(activity1, activity2, 1)
            
            # Weighted average
            return (theme_similarity * 0.7 + activity_similarity * 0.3)
            
        except Exception as e:
            print(f"Error calculating user similarity: {e}")
            return 0.0
    
    def get_comprehensive_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive personalized recommendations."""
        try:
            personalized_themes = self.get_personalized_themes(user_id)
            optimal_time = self.get_optimal_upload_time(user_id)
            similar_users = self.find_similar_users(user_id)
            success_patterns = self.get_success_patterns(user_id)
            
            return {
                "user_id": user_id,
                "personalized_themes": personalized_themes,
                "optimal_upload_time": optimal_time,
                "similar_users": similar_users,
                "success_patterns": success_patterns,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating comprehensive recommendations: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
