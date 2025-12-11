# MoodRhythm

A typing-behavior mood pattern analyzer that passively analyzes typing speed, pause length, burst typing, and rhythm patterns to show mood shifts without reading any text.

## Overview

MoodRhythm captures keyboard timing data (not actual keystrokes) to detect emotional patterns in your typing behavior. It provides real-time visualizations of your mood state, energy levels, and weekly typing rhythms.

## Features

### Typing Pattern Capture

- Keypress intervals (time between consecutive keys)
- Words-per-minute estimation
- Pause detection (gaps greater than 2 seconds)
- Burst detection (rapid typing under 50ms intervals)

### Mood Detection

The analyzer identifies four mood states based on typing patterns:

| Mood State | Typing Indicators |
|------------|-------------------|
| Focused | Steady rhythm, consistent WPM, low pause frequency |
| Stressed | Fast bursts, irregular rhythm, high variability |
| Relaxed | Slower WPM, natural pauses, smooth rhythm |
| Fatigued | Declining WPM over time, increasing pause frequency |

### Visualizations

- Mood Shift Timeline: Line chart showing mood transitions over time
- Energy Score Gauge: Circular gauge displaying typing energy (0-100)
- Weekly Rhythm Heatmap: Hour-by-day activity visualization
- Interval Distribution: Histogram of keypress timing patterns
- WPM Trend Chart: Typing speed changes over time

### Streamlit Dashboard

- Real-time stats display (WPM, Energy Score, Keypresses, Current Mood)
- Start/Stop session controls
- Interactive visualizations
- Historical statistics and weekly trends
- Premium dark theme UI

## Privacy

MoodRhythm is designed with privacy as a core principle:

- No keystroke text is ever stored
- Only timing metadata is recorded (timestamps, intervals)
- All data remains local on your machine
- No network requests or external data transmission
- SQLite database stores only timing information

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/abhi3114-glitch/MoodRhythm.git
cd MoodRhythm
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard will open in your browser at http://localhost:8501

### Dashboard Controls

1. Click Start to begin capturing typing patterns
2. Type in any application (the logger runs in the background)
3. Watch real-time updates of your mood and energy
4. Click Stop to end the session and save data
5. Use Refresh Data to update historical charts
6. Use Clear All Data to reset the database

### Testing the Logger Standalone

Test the typing logger independently:

```bash
python -c "from src.typing_logger import TypingLogger; import time; logger = TypingLogger(); logger.start(); print('Typing...'); time.sleep(30); print(logger.stop())"
```

## Project Structure

```
MoodRhythm/
├── src/
│   ├── __init__.py
│   ├── typing_logger.py    # Keyboard event capture using pynput
│   ├── data_store.py       # SQLite storage for timing logs
│   ├── mood_analyzer.py    # Mood detection algorithms
│   └── visualizations.py   # Matplotlib chart generation
├── app.py                  # Streamlit dashboard
├── requirements.txt        # Python dependencies
├── mood_rhythm.db          # SQLite database (created on first run)
└── README.md
```

## Data Model

### typing_logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | REAL | Unix timestamp in milliseconds |
| interval | REAL | Milliseconds since last keypress |
| is_pause | BOOLEAN | True if interval exceeds 2000ms |
| is_burst | BOOLEAN | True if interval is under 50ms |
| session_id | TEXT | Groups events by session |

### sessions Table

| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT | Primary key |
| start_time | REAL | Session start timestamp |
| end_time | REAL | Session end timestamp |
| total_keypresses | INTEGER | Total keys in session |
| avg_wpm | REAL | Average words per minute |
| mood_score | REAL | Overall mood score |

## Technical Details

### Dependencies

- pynput: Cross-platform keyboard event monitoring
- streamlit: Web dashboard framework
- matplotlib: Visualization library
- pandas: Data manipulation
- numpy: Numerical computations

### Mood Analysis Algorithm

The mood analyzer uses multiple metrics:

1. Coefficient of Variation (CV) of intervals for rhythm consistency
2. Burst ratio (percentage of rapid keypresses)
3. Pause ratio (percentage of long gaps)
4. WPM trends over time

Energy score is calculated as a weighted combination of:

- Speed component (faster typing equals higher energy)
- Burst component (more bursts equals higher energy)
- Pause penalty (more pauses equals lower energy)

## Troubleshooting

### Keyboard Access on macOS

On macOS, you may need to grant accessibility permissions:

1. Go to System Preferences, then Security and Privacy, then Privacy, then Accessibility
2. Add your terminal application or Python executable

### Dashboard Not Updating

If the dashboard is not showing real-time updates:

1. Ensure the logger is started (green Recording Active status)
2. The dashboard auto-refreshes every 500ms while logging
3. Click Refresh Data to manually update historical charts

### Permission Issues on Windows

Run your terminal as Administrator if you encounter keyboard access issues.

## License

This project is provided as-is for educational and personal use.
