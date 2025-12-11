"""
Visualizations Module
Matplotlib-based charts for mood and typing pattern visualization.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from typing import List, Dict, Optional
import io
import base64


# Color scheme
COLORS = {
    'primary': '#6366f1',      # Indigo
    'secondary': '#8b5cf6',    # Purple
    'success': '#10b981',      # Emerald
    'warning': '#f59e0b',      # Amber
    'danger': '#ef4444',       # Red
    'background': '#1e1b4b',   # Dark indigo
    'surface': '#312e81',      # Medium indigo
    'text': '#e0e7ff',         # Light indigo
    'muted': '#6366f180',      # Semi-transparent
}

MOOD_COLORS = {
    'Focused': '#10b981',    # Green
    'Stressed': '#ef4444',   # Red
    'Relaxed': '#3b82f6',    # Blue
    'Fatigued': '#f59e0b',   # Amber
    'Neutral': '#6b7280',    # Gray
}


def set_dark_style():
    """Configure matplotlib for dark theme."""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': COLORS['background'],
        'axes.facecolor': COLORS['surface'],
        'axes.edgecolor': COLORS['muted'],
        'axes.labelcolor': COLORS['text'],
        'text.color': COLORS['text'],
        'xtick.color': COLORS['text'],
        'ytick.color': COLORS['text'],
        'grid.color': COLORS['muted'],
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
    })


def create_mood_shift_graph(timeline: List[Dict], figsize: tuple = (10, 4)) -> plt.Figure:
    """
    Create a mood shift graph showing mood transitions over time.
    
    Args:
        timeline: List of mood snapshots with timestamp, mood, and energy.
        figsize: Figure size tuple.
    
    Returns:
        Matplotlib figure.
    """
    set_dark_style()
    fig, ax = plt.subplots(figsize=figsize)
    
    if not timeline:
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                fontsize=14, color=COLORS['text'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig
    
    # Map moods to numeric values for plotting
    mood_map = {'Focused': 4, 'Stressed': 3, 'Neutral': 2, 'Relaxed': 1, 'Fatigued': 0}
    
    times = [t['timestamp'] for t in timeline]
    moods = [mood_map.get(t['mood'], 2) for t in timeline]
    energies = [t['energy_score'] for t in timeline]
    mood_names = [t['mood'] for t in timeline]
    
    # Normalize time to relative minutes
    start_time = min(times)
    times_relative = [(t - start_time) / 60000 for t in times]  # Convert to minutes
    
    # Plot mood line
    for i in range(len(times_relative)):
        color = MOOD_COLORS.get(mood_names[i], COLORS['muted'])
        if i < len(times_relative) - 1:
            ax.plot(times_relative[i:i+2], moods[i:i+2], color=color, linewidth=2.5)
        ax.scatter([times_relative[i]], [moods[i]], color=color, s=60, zorder=5)
    
    # Add energy as area below
    ax.fill_between(times_relative, [e/25 for e in energies], alpha=0.2, color=COLORS['primary'])
    
    # Customize axes
    ax.set_xlabel('Time (minutes)', fontsize=10)
    ax.set_ylabel('Mood State', fontsize=10)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(['Fatigued', 'Relaxed', 'Neutral', 'Stressed', 'Focused'])
    ax.set_title('Mood Shift Over Time', fontsize=12, fontweight='bold', pad=10)
    
    # Legend
    legend_patches = [mpatches.Patch(color=color, label=mood) 
                      for mood, color in MOOD_COLORS.items()]
    ax.legend(handles=legend_patches, loc='upper right', fontsize=8)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    return fig


def create_energy_gauge(energy_score: int, figsize: tuple = (4, 4)) -> plt.Figure:
    """
    Create a circular gauge displaying typing energy score.
    
    Args:
        energy_score: Energy score from 0-100.
        figsize: Figure size tuple.
    
    Returns:
        Matplotlib figure.
    """
    set_dark_style()
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
    
    # Configure the gauge
    theta_start = np.pi
    theta_end = 0
    
    # Background arc
    theta_bg = np.linspace(theta_start, theta_end, 100)
    ax.plot(theta_bg, [1] * 100, color=COLORS['muted'], linewidth=20, solid_capstyle='round')
    
    # Energy arc
    energy_angle = theta_start - (energy_score / 100) * np.pi
    theta_energy = np.linspace(theta_start, energy_angle, 100)
    
    # Color based on energy level
    if energy_score >= 70:
        color = COLORS['success']
    elif energy_score >= 40:
        color = COLORS['warning']
    else:
        color = COLORS['danger']
    
    ax.plot(theta_energy, [1] * len(theta_energy), color=color, linewidth=20, solid_capstyle='round')
    
    # Center text
    ax.annotate(f'{energy_score}', xy=(np.pi/2, 0), ha='center', va='center',
                fontsize=32, fontweight='bold', color=COLORS['text'])
    ax.annotate('Energy', xy=(np.pi/2, -0.35), ha='center', va='center',
                fontsize=12, color=COLORS['text'], alpha=0.8)
    
    # Hide unnecessary elements
    ax.set_ylim(0, 1.2)
    ax.set_theta_zero_location('S')
    ax.set_theta_direction(-1)
    ax.axis('off')
    
    plt.tight_layout()
    return fig


def create_weekly_heatmap(activity_matrix: List[List[int]], figsize: tuple = (10, 4)) -> plt.Figure:
    """
    Create a heatmap showing typing activity by day and hour.
    
    Args:
        activity_matrix: 7x24 matrix of activity counts.
        figsize: Figure size tuple.
    
    Returns:
        Matplotlib figure.
    """
    set_dark_style()
    fig, ax = plt.subplots(figsize=figsize)
    
    if not activity_matrix or not any(any(row) for row in activity_matrix):
        ax.text(0.5, 0.5, 'No weekly data available yet', ha='center', va='center',
                fontsize=14, color=COLORS['text'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig
    
    # Convert to numpy array
    data = np.array(activity_matrix)
    
    # Create custom colormap
    cmap = LinearSegmentedColormap.from_list('custom', 
        [COLORS['background'], COLORS['primary'], COLORS['success']], N=256)
    
    # Create heatmap
    im = ax.imshow(data, cmap=cmap, aspect='auto', interpolation='nearest')
    
    # Configure axes
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    hours = [f'{h}:00' for h in range(0, 24, 3)]
    
    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels(hours, fontsize=8)
    ax.set_yticks(range(7))
    ax.set_yticklabels(days, fontsize=10)
    
    ax.set_xlabel('Hour of Day', fontsize=10)
    ax.set_ylabel('Day of Week', fontsize=10)
    ax.set_title('Weekly Typing Activity', fontsize=12, fontweight='bold', pad=10)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Keypresses', fontsize=9)
    
    plt.tight_layout()
    return fig


def create_interval_distribution(events: List[Dict], figsize: tuple = (8, 4)) -> plt.Figure:
    """
    Create a histogram of keypress intervals.
    
    Args:
        events: List of typing events.
        figsize: Figure size tuple.
    
    Returns:
        Matplotlib figure.
    """
    set_dark_style()
    fig, ax = plt.subplots(figsize=figsize)
    
    intervals = [e['interval'] for e in events if e.get('interval') is not None and e['interval'] < 2000]
    
    if not intervals:
        ax.text(0.5, 0.5, 'No interval data available', ha='center', va='center',
                fontsize=14, color=COLORS['text'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig
    
    # Create histogram
    n, bins, patches = ax.hist(intervals, bins=50, color=COLORS['primary'], 
                                edgecolor=COLORS['background'], alpha=0.8)
    
    # Color bars based on typing speed
    for i, patch in enumerate(patches):
        if bins[i] < 50:
            patch.set_facecolor(COLORS['danger'])  # Burst
        elif bins[i] < 150:
            patch.set_facecolor(COLORS['success'])  # Normal
        else:
            patch.set_facecolor(COLORS['warning'])  # Slow
    
    # Add vertical lines for thresholds
    ax.axvline(x=50, color=COLORS['danger'], linestyle='--', alpha=0.7, label='Burst (<50ms)')
    ax.axvline(x=150, color=COLORS['success'], linestyle='--', alpha=0.7, label='Normal')
    
    ax.set_xlabel('Interval (ms)', fontsize=10)
    ax.set_ylabel('Frequency', fontsize=10)
    ax.set_title('Keypress Interval Distribution', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', fontsize=8)
    
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    return fig


def create_wpm_trend(timeline: List[Dict], figsize: tuple = (10, 3)) -> plt.Figure:
    """
    Create a WPM trend line chart.
    
    Args:
        timeline: List of mood snapshots with WPM data.
        figsize: Figure size tuple.
    
    Returns:
        Matplotlib figure.
    """
    set_dark_style()
    fig, ax = plt.subplots(figsize=figsize)
    
    if not timeline:
        ax.text(0.5, 0.5, 'No WPM data available', ha='center', va='center',
                fontsize=14, color=COLORS['text'])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        return fig
    
    times = [t['timestamp'] for t in timeline]
    wpms = [t['wpm'] for t in timeline]
    
    # Normalize time
    start_time = min(times)
    times_relative = [(t - start_time) / 60000 for t in times]
    
    # Plot WPM line
    ax.plot(times_relative, wpms, color=COLORS['primary'], linewidth=2.5, marker='o', markersize=4)
    ax.fill_between(times_relative, wpms, alpha=0.3, color=COLORS['primary'])
    
    # Add average line
    avg_wpm = sum(wpms) / len(wpms)
    ax.axhline(y=avg_wpm, color=COLORS['success'], linestyle='--', alpha=0.7,
               label=f'Average: {avg_wpm:.0f} WPM')
    
    ax.set_xlabel('Time (minutes)', fontsize=10)
    ax.set_ylabel('Words Per Minute', fontsize=10)
    ax.set_title('Typing Speed Over Time', fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='upper right', fontsize=8)
    
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    
    return fig


def fig_to_base64(fig: plt.Figure) -> str:
    """Convert a matplotlib figure to base64 string for embedding."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_str


if __name__ == '__main__':
    # Test visualizations
    import time
    
    # Generate test data
    base_time = time.time() * 1000
    test_timeline = [
        {'timestamp': base_time, 'mood': 'Neutral', 'energy_score': 50, 'wpm': 40},
        {'timestamp': base_time + 60000, 'mood': 'Focused', 'energy_score': 75, 'wpm': 55},
        {'timestamp': base_time + 120000, 'mood': 'Stressed', 'energy_score': 85, 'wpm': 65},
        {'timestamp': base_time + 180000, 'mood': 'Relaxed', 'energy_score': 45, 'wpm': 35},
        {'timestamp': base_time + 240000, 'mood': 'Fatigued', 'energy_score': 30, 'wpm': 25},
    ]
    
    # Test mood graph
    fig = create_mood_shift_graph(test_timeline)
    plt.savefig('test_mood_graph.png')
    print("Created test_mood_graph.png")
    
    # Test energy gauge
    fig = create_energy_gauge(72)
    plt.savefig('test_energy_gauge.png')
    print("Created test_energy_gauge.png")
    
    print("Visualization tests completed!")
