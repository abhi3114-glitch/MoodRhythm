"""
Mood Analyzer Module
Analyzes typing patterns to detect mood states and calculate energy scores.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np


class MoodAnalyzer:
    """
    Analyzes typing patterns to detect mood indicators.
    
    Mood States:
    - Focused: Steady rhythm, consistent WPM, low pause frequency
    - Stressed: Fast bursts, irregular rhythm, high variability
    - Relaxed: Slower WPM, longer natural pauses, smooth rhythm
    - Fatigued: Declining WPM, increasing pauses over time
    """
    
    # Mood state constants
    MOOD_FOCUSED = "Focused"
    MOOD_STRESSED = "Stressed"
    MOOD_RELAXED = "Relaxed"
    MOOD_FATIGUED = "Fatigued"
    MOOD_NEUTRAL = "Neutral"
    
    def __init__(self):
        """Initialize the mood analyzer."""
        # Thresholds for mood detection
        self.HIGH_WPM_THRESHOLD = 60
        self.LOW_WPM_THRESHOLD = 30
        self.HIGH_BURST_RATIO = 0.3  # 30% of keypresses are bursts
        self.HIGH_PAUSE_RATIO = 0.1  # 10% of keypresses are pauses
        self.RHYTHM_CONSISTENCY_THRESHOLD = 0.3  # CV < 0.3 = consistent
    
    def calculate_energy_score(self, events: List[Dict], wpm: float = None) -> int:
        """
        Calculate typing energy score (0-100).
        
        Higher score = more energetic typing pattern.
        
        Args:
            events: List of typing events.
            wpm: Current WPM (optional, calculated if not provided).
        
        Returns:
            Energy score from 0-100.
        """
        if not events:
            return 50  # Neutral score
        
        intervals = [e['interval'] for e in events if e.get('interval') is not None]
        if not intervals:
            return 50
        
        # Calculate components
        burst_count = sum(1 for e in events if e.get('is_burst', False))
        pause_count = sum(1 for e in events if e.get('is_pause', False))
        
        # Speed component (faster = higher energy)
        avg_interval = np.mean(intervals)
        speed_score = max(0, min(100, 100 - (avg_interval / 10)))  # Normalize
        
        # Burst component (more bursts = higher energy)
        burst_ratio = burst_count / len(events) if events else 0
        burst_score = min(100, burst_ratio * 300)  # Scale up
        
        # Pause penalty (more pauses = lower energy)
        pause_ratio = pause_count / len(events) if events else 0
        pause_penalty = pause_ratio * 50
        
        # Combine components
        energy = (speed_score * 0.4 + burst_score * 0.4) - pause_penalty
        
        # Boost with WPM if available
        if wpm:
            wpm_factor = min(1.5, wpm / 40)  # 40 WPM = baseline
            energy *= wpm_factor
        
        return max(0, min(100, int(energy)))
    
    def detect_mood(self, events: List[Dict], wpm: float = None) -> Dict:
        """
        Detect current mood based on typing patterns.
        
        Args:
            events: List of typing events.
            wpm: Current WPM (optional).
        
        Returns:
            Dictionary with mood state and confidence.
        """
        if not events or len(events) < 10:
            return {
                'mood': self.MOOD_NEUTRAL,
                'confidence': 0.0,
                'indicators': {}
            }
        
        intervals = [e['interval'] for e in events if e.get('interval') is not None]
        if len(intervals) < 5:
            return {
                'mood': self.MOOD_NEUTRAL,
                'confidence': 0.0,
                'indicators': {}
            }
        
        # Calculate metrics
        avg_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        cv = std_interval / avg_interval if avg_interval > 0 else 0  # Coefficient of variation
        
        burst_count = sum(1 for e in events if e.get('is_burst', False))
        pause_count = sum(1 for e in events if e.get('is_pause', False))
        
        burst_ratio = burst_count / len(events)
        pause_ratio = pause_count / len(events)
        
        # Estimate WPM if not provided
        if wpm is None:
            session_duration = (events[-1]['timestamp'] - events[0]['timestamp']) / 1000 / 60  # minutes
            wpm = (len(events) / 5) / max(session_duration, 0.01) if session_duration > 0 else 0
        
        indicators = {
            'avg_interval': round(avg_interval, 1),
            'rhythm_consistency': round(1 - min(cv, 1), 2),  # Higher = more consistent
            'burst_ratio': round(burst_ratio, 3),
            'pause_ratio': round(pause_ratio, 3),
            'wpm': round(wpm, 1)
        }
        
        # Mood detection logic
        mood = self.MOOD_NEUTRAL
        confidence = 0.5
        
        # High consistency + good WPM = Focused
        if cv < self.RHYTHM_CONSISTENCY_THRESHOLD and wpm > 35:
            mood = self.MOOD_FOCUSED
            confidence = 0.7 + (0.3 * (1 - cv))
        
        # High bursts + irregular rhythm = Stressed
        elif burst_ratio > self.HIGH_BURST_RATIO and cv > 0.5:
            mood = self.MOOD_STRESSED
            confidence = 0.6 + (burst_ratio * 0.4)
        
        # Slow WPM + natural pauses = Relaxed
        elif wpm < self.LOW_WPM_THRESHOLD and pause_ratio < self.HIGH_PAUSE_RATIO:
            mood = self.MOOD_RELAXED
            confidence = 0.6 + (0.4 * (1 - wpm / 30))
        
        # Many pauses + declining pattern = Fatigued
        elif pause_ratio > self.HIGH_PAUSE_RATIO:
            mood = self.MOOD_FATIGUED
            confidence = 0.5 + (pause_ratio * 2)
        
        return {
            'mood': mood,
            'confidence': min(confidence, 1.0),
            'indicators': indicators
        }
    
    def analyze_session(self, events: List[Dict]) -> Dict:
        """
        Comprehensive analysis of a typing session.
        
        Args:
            events: List of typing events.
        
        Returns:
            Complete session analysis.
        """
        if not events:
            return {
                'mood': self.MOOD_NEUTRAL,
                'energy_score': 50,
                'wpm': 0,
                'total_keypresses': 0,
                'duration_seconds': 0,
                'indicators': {}
            }
        
        # Calculate duration
        if len(events) >= 2:
            duration_ms = events[-1]['timestamp'] - events[0]['timestamp']
            duration_seconds = duration_ms / 1000
            duration_minutes = duration_seconds / 60
        else:
            duration_seconds = 0
            duration_minutes = 0
        
        # Calculate WPM
        wpm = (len(events) / 5) / max(duration_minutes, 0.01)
        
        # Detect mood
        mood_result = self.detect_mood(events, wpm)
        
        # Calculate energy
        energy_score = self.calculate_energy_score(events, wpm)
        
        return {
            'mood': mood_result['mood'],
            'mood_confidence': mood_result['confidence'],
            'energy_score': energy_score,
            'wpm': round(wpm, 1),
            'total_keypresses': len(events),
            'duration_seconds': round(duration_seconds, 1),
            'indicators': mood_result['indicators']
        }
    
    def calculate_mood_timeline(self, events: List[Dict], window_size: int = 30) -> List[Dict]:
        """
        Calculate mood over time using a sliding window.
        
        Args:
            events: List of typing events.
            window_size: Number of events per window.
        
        Returns:
            List of mood snapshots over time.
        """
        if len(events) < window_size:
            analysis = self.analyze_session(events)
            return [{
                'timestamp': events[-1]['timestamp'] if events else 0,
                'mood': analysis['mood'],
                'energy_score': analysis['energy_score'],
                'wpm': analysis['wpm']
            }]
        
        timeline = []
        step = max(1, window_size // 2)  # 50% overlap
        
        for i in range(0, len(events) - window_size + 1, step):
            window = events[i:i + window_size]
            analysis = self.analyze_session(window)
            
            timeline.append({
                'timestamp': window[-1]['timestamp'],
                'mood': analysis['mood'],
                'energy_score': analysis['energy_score'],
                'wpm': analysis['wpm']
            })
        
        return timeline
    
    def get_weekly_rhythm(self, hourly_stats: List[Dict]) -> Dict:
        """
        Analyze weekly rhythm patterns from hourly stats.
        
        Args:
            hourly_stats: List of hourly stat dictionaries.
        
        Returns:
            Dictionary with weekly rhythm analysis.
        """
        if not hourly_stats:
            return {
                'peak_hour': None,
                'peak_day': None,
                'activity_matrix': [],
                'insights': []
            }
        
        # Create activity matrix (7 days x 24 hours)
        activity_matrix = [[0 for _ in range(24)] for _ in range(7)]
        
        for stat in hourly_stats:
            day = stat['day_of_week']
            hour = stat['hour']
            activity_matrix[day][hour] = stat['keypress_count']
        
        # Find peaks
        max_activity = 0
        peak_hour = 0
        peak_day = 0
        
        for day in range(7):
            for hour in range(24):
                if activity_matrix[day][hour] > max_activity:
                    max_activity = activity_matrix[day][hour]
                    peak_hour = hour
                    peak_day = day
        
        # Generate insights
        insights = []
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        if max_activity > 0:
            insights.append(f"Peak activity: {day_names[peak_day]} at {peak_hour}:00")
        
        # Calculate daily totals
        daily_totals = [sum(row) for row in activity_matrix]
        if any(daily_totals):
            most_active_day = daily_totals.index(max(daily_totals))
            insights.append(f"Most active day: {day_names[most_active_day]}")
        
        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'activity_matrix': activity_matrix,
            'insights': insights
        }


if __name__ == '__main__':
    # Test the mood analyzer
    import time
    
    analyzer = MoodAnalyzer()
    
    # Generate test events
    base_time = time.time() * 1000
    test_events = []
    
    # Simulate focused typing (consistent intervals)
    for i in range(50):
        test_events.append({
            'timestamp': base_time + i * 100,
            'interval': 100 + np.random.normal(0, 10),
            'is_pause': False,
            'is_burst': False
        })
    
    analysis = analyzer.analyze_session(test_events)
    print(f"Session Analysis:")
    print(f"  Mood: {analysis['mood']}")
    print(f"  Energy Score: {analysis['energy_score']}")
    print(f"  WPM: {analysis['wpm']}")
    print(f"  Indicators: {analysis['indicators']}")
