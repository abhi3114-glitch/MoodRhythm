"""
Typing Logger Module
Captures keyboard timing data (intervals, pauses, bursts) without storing actual keystrokes.
Privacy-first design: only timing metadata is recorded.
"""

import time
import threading
import uuid
from typing import Callable, Optional
from pynput import keyboard


class TypingLogger:
    """
    Captures typing timing patterns without recording actual keystrokes.
    Uses pynput for keyboard event monitoring.
    """
    
    def __init__(self, on_event_callback: Optional[Callable] = None):
        """
        Initialize the typing logger.
        
        Args:
            on_event_callback: Optional callback function called on each keypress event.
                              Receives a dict with timing data.
        """
        self.listener: Optional[keyboard.Listener] = None
        self.is_running = False
        self.session_id = None
        
        # Timing state
        self.last_keypress_time: Optional[float] = None
        self.keypress_count = 0
        self.session_start_time: Optional[float] = None
        
        # Thresholds (in milliseconds)
        self.PAUSE_THRESHOLD = 2000  # Gap > 2s = pause
        self.BURST_THRESHOLD = 50    # Gap < 50ms = burst typing
        
        # Callback for real-time updates
        self.on_event_callback = on_event_callback
        
        # Event storage for current session
        self.events = []
        
        # Lock for thread safety
        self._lock = threading.Lock()
    
    def _on_press(self, key):
        """Handle keypress events - records timing only, not the key itself."""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        with self._lock:
            interval = None
            is_pause = False
            is_burst = False
            
            if self.last_keypress_time is not None:
                interval = current_time - self.last_keypress_time
                is_pause = interval > self.PAUSE_THRESHOLD
                is_burst = interval < self.BURST_THRESHOLD
            
            self.last_keypress_time = current_time
            self.keypress_count += 1
            
            event = {
                'timestamp': current_time,
                'interval': interval,
                'is_pause': is_pause,
                'is_burst': is_burst,
                'session_id': self.session_id
            }
            
            self.events.append(event)
            
            # Call the callback if provided
            if self.on_event_callback:
                self.on_event_callback(event)
    
    def start(self) -> str:
        """
        Start capturing typing events.
        
        Returns:
            Session ID for this logging session.
        """
        if self.is_running:
            return self.session_id
        
        self.session_id = str(uuid.uuid4())
        self.session_start_time = time.time() * 1000
        self.last_keypress_time = None
        self.keypress_count = 0
        self.events = []
        
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()
        self.is_running = True
        
        return self.session_id
    
    def stop(self) -> dict:
        """
        Stop capturing typing events.
        
        Returns:
            Session summary with statistics.
        """
        if not self.is_running:
            return {}
        
        self.listener.stop()
        self.is_running = False
        
        session_duration = (time.time() * 1000 - self.session_start_time) / 1000  # in seconds
        
        return {
            'session_id': self.session_id,
            'duration_seconds': session_duration,
            'total_keypresses': self.keypress_count,
            'events': self.events.copy()
        }
    
    def get_current_stats(self) -> dict:
        """Get real-time statistics for the current session."""
        with self._lock:
            if not self.is_running or not self.events:
                return {
                    'wpm': 0,
                    'avg_interval': 0,
                    'pause_count': 0,
                    'burst_count': 0,
                    'keypress_count': 0,
                    'session_duration': 0
                }
            
            # Calculate WPM (average word = 5 characters)
            session_duration = (time.time() * 1000 - self.session_start_time) / 1000 / 60  # in minutes
            wpm = (self.keypress_count / 5) / max(session_duration, 0.01)
            
            # Calculate average interval
            intervals = [e['interval'] for e in self.events if e['interval'] is not None]
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            # Count pauses and bursts
            pause_count = sum(1 for e in self.events if e['is_pause'])
            burst_count = sum(1 for e in self.events if e['is_burst'])
            
            return {
                'wpm': round(wpm, 1),
                'avg_interval': round(avg_interval, 1),
                'pause_count': pause_count,
                'burst_count': burst_count,
                'keypress_count': self.keypress_count,
                'session_duration': round(session_duration * 60, 1)  # back to seconds
            }
    
    def get_events(self) -> list:
        """Get all events from current session."""
        with self._lock:
            return self.events.copy()


if __name__ == '__main__':
    # Simple test
    def on_event(event):
        if event['interval']:
            print(f"Interval: {event['interval']:.0f}ms, Pause: {event['is_pause']}, Burst: {event['is_burst']}")
    
    logger = TypingLogger(on_event_callback=on_event)
    print("Starting typing logger... Press Ctrl+C to stop.")
    logger.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        summary = logger.stop()
        print(f"\nSession Summary:")
        print(f"  Duration: {summary['duration_seconds']:.1f}s")
        print(f"  Total keypresses: {summary['total_keypresses']}")
