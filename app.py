"""
MoodRhythm - Typing-Behavior Mood Pattern Analyzer
Streamlit Dashboard for real-time mood tracking based on typing patterns.
"""

import streamlit as st
import time
import threading
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.typing_logger import TypingLogger
from src.data_store import DataStore
from src.mood_analyzer import MoodAnalyzer
from src.visualizations import (
    create_mood_shift_graph,
    create_energy_gauge,
    create_weekly_heatmap,
    create_interval_distribution,
    create_wpm_trend
)

# Page configuration
st.set_page_config(
    page_title="MoodRhythm",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium dark theme
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #a5b4fc;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.6);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #e0e7ff;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #a5b4fc;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Mood indicator */
    .mood-badge {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        border-radius: 30px;
        font-weight: 600;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .mood-focused { background: linear-gradient(135deg, #10b981, #059669); color: white; }
    .mood-stressed { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; }
    .mood-relaxed { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; }
    .mood-fatigued { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; }
    .mood-neutral { background: linear-gradient(135deg, #6b7280, #4b5563); color: white; }
    
    /* Section headers */
    .section-header {
        color: #c7d2fe;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
    }
    
    /* Status indicator */
    .status-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-active { background: #10b981; }
    .status-inactive { background: #6b7280; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Privacy badge */
    .privacy-badge {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #10b981;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Chart container */
    .chart-container {
        background: rgba(49, 46, 129, 0.5);
        border-radius: 16px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(30, 27, 75, 0.9);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Insights list */
    .insight-item {
        background: rgba(99, 102, 241, 0.1);
        border-left: 3px solid #6366f1;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        color: #e0e7ff;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    if 'logger' not in st.session_state:
        st.session_state.logger = TypingLogger()
    if 'data_store' not in st.session_state:
        st.session_state.data_store = DataStore()
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = MoodAnalyzer()
    if 'is_logging' not in st.session_state:
        st.session_state.is_logging = False
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()


def start_logging():
    """Start the typing logger."""
    st.session_state.logger.start()
    st.session_state.is_logging = True


def stop_logging():
    """Stop the typing logger and save data."""
    if st.session_state.is_logging:
        summary = st.session_state.logger.stop()
        if summary and summary.get('events'):
            st.session_state.data_store.save_events(summary['events'])
            st.session_state.data_store.save_session({
                'session_id': summary['session_id'],
                'start_time': summary['events'][0]['timestamp'] if summary['events'] else None,
                'end_time': summary['events'][-1]['timestamp'] if summary['events'] else None,
                'total_keypresses': summary['total_keypresses'],
            })
        st.session_state.is_logging = False


def get_mood_class(mood: str) -> str:
    """Get CSS class for mood badge."""
    return f"mood-{mood.lower()}"


def main():
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎵 MoodRhythm</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Understand your mood through typing patterns — without reading what you type</p>', unsafe_allow_html=True)
    
    # Privacy badge
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('''
            <div style="text-align: center;">
                <span class="privacy-badge">
                    🔒 Privacy-First: No keystrokes stored, only timing
                </span>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### ⚙️ Controls")
        
        # Status indicator
        if st.session_state.is_logging:
            st.markdown('''
                <div style="margin: 1rem 0;">
                    <span class="status-dot status-active"></span>
                    <span style="color: #10b981; font-weight: 600;">Recording Active</span>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
                <div style="margin: 1rem 0;">
                    <span class="status-dot status-inactive"></span>
                    <span style="color: #6b7280; font-weight: 600;">Recording Stopped</span>
                </div>
            ''', unsafe_allow_html=True)
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start", disabled=st.session_state.is_logging, use_container_width=True):
                start_logging()
                st.rerun()
        with col2:
            if st.button("⏹️ Stop", disabled=not st.session_state.is_logging, use_container_width=True):
                stop_logging()
                st.rerun()
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        # Clear data button
        if st.button("🗑️ Clear All Data", use_container_width=True):
            st.session_state.data_store.clear_all_data()
            st.success("Data cleared!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.markdown("""
            MoodRhythm analyzes your typing patterns to detect mood shifts:
            
            - **Focused**: Steady rhythm, consistent speed
            - **Stressed**: Fast bursts, irregular patterns
            - **Relaxed**: Slower pace, natural pauses
            - **Fatigued**: Declining speed, more pauses
        """)
    
    # Get current data
    current_stats = st.session_state.logger.get_current_stats() if st.session_state.is_logging else {}
    current_events = st.session_state.logger.get_events() if st.session_state.is_logging else []
    
    # Analyze current session
    if current_events:
        analysis = st.session_state.analyzer.analyze_session(current_events)
    else:
        # Load historical data
        historical_events = st.session_state.data_store.get_events_last_n_days(7)
        if historical_events:
            analysis = st.session_state.analyzer.analyze_session(historical_events)
        else:
            analysis = {
                'mood': 'Neutral',
                'mood_confidence': 0,
                'energy_score': 50,
                'wpm': 0,
                'total_keypresses': 0,
                'duration_seconds': 0
            }
    
    # Main metrics row
    st.markdown('<div class="section-header">📈 Current Session</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        wpm = current_stats.get('wpm', analysis.get('wpm', 0))
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{wpm:.0f}</div>
                <div class="metric-label">Words/Min</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        energy = analysis.get('energy_score', 50)
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{energy}</div>
                <div class="metric-label">Energy Score</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        keypresses = current_stats.get('keypress_count', analysis.get('total_keypresses', 0))
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{keypresses}</div>
                <div class="metric-label">Keypresses</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        mood = analysis.get('mood', 'Neutral')
        mood_class = get_mood_class(mood)
        st.markdown(f'''
            <div class="metric-card">
                <span class="mood-badge {mood_class}">{mood}</span>
                <div class="metric-label" style="margin-top: 0.5rem;">Current Mood</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-header">🎭 Mood Shift Timeline</div>', unsafe_allow_html=True)
        
        # Get mood timeline
        events_for_timeline = current_events if current_events else st.session_state.data_store.get_events_last_n_days(1)
        if events_for_timeline:
            timeline = st.session_state.analyzer.calculate_mood_timeline(events_for_timeline)
            fig = create_mood_shift_graph(timeline)
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("Start typing to see your mood shift over time")
    
    with col2:
        st.markdown('<div class="section-header">⚡ Energy Level</div>', unsafe_allow_html=True)
        fig = create_energy_gauge(analysis.get('energy_score', 50))
        st.pyplot(fig, use_container_width=True)
    
    # Weekly rhythm section
    st.markdown('<div class="section-header">📅 Weekly Rhythm</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        hourly_stats = st.session_state.data_store.get_hourly_stats(7)
        weekly_rhythm = st.session_state.analyzer.get_weekly_rhythm(hourly_stats)
        fig = create_weekly_heatmap(weekly_rhythm['activity_matrix'])
        st.pyplot(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 💡 Insights")
        if weekly_rhythm.get('insights'):
            for insight in weekly_rhythm['insights']:
                st.markdown(f'<div class="insight-item">{insight}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="insight-item">Keep typing to generate insights</div>', unsafe_allow_html=True)
    
    # Interval distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">⏱️ Interval Distribution</div>', unsafe_allow_html=True)
        all_events = current_events if current_events else st.session_state.data_store.get_events_last_n_days(7)
        fig = create_interval_distribution(all_events)
        st.pyplot(fig, use_container_width=True)
    
    with col2:
        st.markdown('<div class="section-header">📈 Speed Trend</div>', unsafe_allow_html=True)
        if events_for_timeline:
            timeline = st.session_state.analyzer.calculate_mood_timeline(events_for_timeline, window_size=20)
            fig = create_wpm_trend(timeline)
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("Start typing to see your speed trend")
    
    # Session statistics
    st.markdown('<div class="section-header">📊 Historical Statistics</div>', unsafe_allow_html=True)
    
    total_stats = st.session_state.data_store.get_total_stats()
    daily_stats = st.session_state.data_store.get_daily_stats(7)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Keypresses", f"{total_stats.get('total_keypresses', 0):,}")
    
    with col2:
        avg_interval = total_stats.get('avg_interval', 0)
        st.metric("Avg Interval", f"{avg_interval:.0f} ms" if avg_interval else "N/A")
    
    with col3:
        st.metric("Total Pauses", f"{total_stats.get('total_pauses', 0):,}")
    
    with col4:
        st.metric("Total Bursts", f"{total_stats.get('total_bursts', 0):,}")
    
    # Auto-refresh while logging
    if st.session_state.is_logging:
        time.sleep(0.5)
        st.rerun()


if __name__ == "__main__":
    main()
