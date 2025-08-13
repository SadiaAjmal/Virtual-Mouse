"""
Professional Hand Mouse Controller
A comprehensive hand gesture-based system controller with cursor control,
clicking, scrolling, gestures, and system functions.

Features:
- Cursor control with index finger
- Left/Right click gestures
- Scrolling with thumb gestures
- Volume and brightness control
- Media controls (play/pause, next/previous)
- Gesture recognition with visual feedback
- Configurable sensitivity and smoothing
- Performance optimizations

Author: Hand Controller Pro
Version: 2.0
"""

import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
from collections import deque
import threading
from enum import Enum

class HandGesture(Enum):
    """Enumeration of recognized hand gestures"""
    CURSOR_CONTROL = "cursor_control"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    BRIGHTNESS_UP = "brightness_up"
    BRIGHTNESS_DOWN = "brightness_down"
    PLAY_PAUSE = "play_pause"
    NEXT_TRACK = "next_track"
    PREV_TRACK = "prev_track"
    DRAG_START = "drag_start"
    DRAG_END = "drag_end"
    NONE = "none"

class HandMouseController:
    """Professional Hand Mouse Controller with advanced gesture recognition"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Performance settings
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.01
        
        # Cursor smoothing
        self.cursor_history = deque(maxlen=5)
        self.smoothing_factor = 0.7
        
        # Gesture control
        self.last_gesture = HandGesture.NONE
        self.gesture_delay = 0.5  # Increased delay between gesture switches
        self.last_gesture_time = 0
        self.click_threshold = 0.04  # Moved to class level
        self.scroll_sensitivity = 5  # Increased scroll speed
        
        # Drag and drop
        self.is_dragging = False
        self.drag_start_pos = None
        
        # Calibration zone (percentage of screen)
        self.calibration_zone = {
            'x_min': 0.1, 'x_max': 0.9,
            'y_min': 0.1, 'y_max': 0.9
        }
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Visual feedback
        self.gesture_display_time = 1.0
        self.last_gesture_display = ""
        self.gesture_display_start = 0
        
        print("Hand Mouse Controller initialized successfully!")
        print("\n=== GESTURE CONTROLS ===")
        print("CURSOR CONTROL:")
        print("  - Index finger only: Move cursor")
        print("\nCLICKING:")
        print("  - Index finger + bring thumb close: Left click")
        print("  - Middle finger + bring thumb close: Right click")
        print("\nSCROLLING:")
        print("  - Thumb up only: Scroll up (faster)")
        print("  - Thumb down only: Scroll down (faster)")
        print("\nVOLUME:")
        print("  - Peace sign (Index + Middle up): Volume up")
        print("  - Closed fist (no fingers): Volume down")
        print("\nMEDIA CONTROLS:")
        print("  - Four fingers up (no thumb): Play/Pause")
        print("  - All five fingers up: Next track (fixed)")
        print("  - Only pinky up: Previous track")
        print("\nBRIGHTNESS:")
        print("  - Thumbs up gesture: Brightness up")
        print("  - Thumbs down gesture: Brightness down")
        print("\nPress 'q' to quit, 'c' for calibration info")
        print("=" * 40)

    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def is_finger_up(self, landmarks, finger_tip, finger_pip):
        """Check if a finger is raised"""
        return landmarks[finger_tip].y < landmarks[finger_pip].y

    def get_finger_states(self, landmarks):
        """Get the state of all fingers (up/down)"""
        finger_states = []
        
        # Thumb (special case - check x-coordinate relative to hand orientation)
        # Compare thumb tip with thumb IP joint
        thumb_is_up = landmarks[4].x > landmarks[3].x if landmarks[4].x > landmarks[17].x else landmarks[4].x < landmarks[3].x
        finger_states.append(thumb_is_up)
        
        # Other fingers - compare tip with PIP joint
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_pips = [6, 10, 14, 18]  # PIP joints
        
        for tip, pip in zip(finger_tips, finger_pips):
            finger_states.append(landmarks[tip].y < landmarks[pip].y)
        
        return finger_states

    def recognize_gesture(self, landmarks):
        """Advanced gesture recognition with corrected finger detection"""
        finger_states = self.get_finger_states(landmarks)
        fingers_up_count = sum(finger_states)
        
        # Get key landmark positions for distance calculations
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        # Calculate distances for gesture detection
        thumb_index_dist = self.calculate_distance(thumb_tip, index_tip)
        thumb_middle_dist = self.calculate_distance(thumb_tip, middle_tip)
        index_middle_dist = self.calculate_distance(index_tip, middle_tip)
        
        # Define distance thresholds
        click_threshold = 0.06  # Increased threshold for better detection
        close_threshold = 0.08
        
        # Debug for right click (uncomment to debug)
        print(f"Thumb: {finger_states[0]}, Middle: {finger_states[2]}, Distance: {thumb_middle_dist:.3f}")
        
        # Gesture Recognition Logic - PRIORITIZE CLICKS FIRST
        
        # LEFT CLICK: Thumb + Index finger touch (both fingers up and close together)
        if (finger_states[0] and finger_states[1] and  # Both thumb and index up
            thumb_index_dist < click_threshold and      # They are close together
            not finger_states[2] and not finger_states[3] and not finger_states[4]):  # Other fingers down
            return HandGesture.LEFT_CLICK
        
        # RIGHT CLICK: Thumb + Middle finger touch - SIMPLIFIED DETECTION
        elif (finger_states[0] and finger_states[2] and  # Both thumb and middle up
              thumb_middle_dist < click_threshold):       # They are close together
            # More flexible - don't require other fingers to be strictly down
            return HandGesture.RIGHT_CLICK
        
        # ALTERNATIVE RIGHT CLICK: Just middle finger up with thumb touching
        elif (finger_states[2] and  # Middle finger up
              thumb_middle_dist < click_threshold and  # Thumb close to middle
              not finger_states[1]):  # Index finger down (to avoid conflict with peace sign)
            return HandGesture.RIGHT_CLICK
        
        # CURSOR CONTROL: Only index finger up (or index + thumb but not close)
        elif (finger_states[1] and not finger_states[2] and not finger_states[3] and not finger_states[4] and
              (not finger_states[0] or thumb_index_dist > click_threshold)):
            return HandGesture.CURSOR_CONTROL
        
        # SCROLL UP: Thumb up only
        elif finger_states[0] and not any(finger_states[1:]):
            # Check if thumb is pointing up (y-coordinate check)
            if thumb_tip.y < landmarks[2].y:  # Thumb tip above thumb CMC joint
                return HandGesture.SCROLL_UP
            else:
                return HandGesture.SCROLL_DOWN
        
        # VOLUME UP: Peace sign (index + middle fingers up, others down) - but not too close to avoid right click
        elif (finger_states == [False, True, True, False, False] and 
              thumb_middle_dist > click_threshold):  # Ensure it's not a right click
            return HandGesture.VOLUME_UP
        
        # VOLUME DOWN: Closed fist (no fingers up)
        elif fingers_up_count == 0:
            return HandGesture.VOLUME_DOWN
        
        # PLAY/PAUSE: Four fingers up (index, middle, ring, pinky - thumb down)
        elif finger_states == [False, True, True, True, True]:
            return HandGesture.PLAY_PAUSE
        
        # NEXT TRACK: All five fingers up (improved detection)
        elif finger_states == [True, True, True, True, True]:
            return HandGesture.NEXT_TRACK
        
        # PREVIOUS TRACK: Only pinky up
        elif finger_states == [False, False, False, False, True]:
            return HandGesture.PREV_TRACK
        
        # BRIGHTNESS UP: Thumbs up (thumb up, others down) - alternative interpretation
        elif finger_states == [True, False, False, False, False] and thumb_tip.y < landmarks[2].y:
            return HandGesture.BRIGHTNESS_UP
        
        # BRIGHTNESS DOWN: Thumbs down (thumb up but pointing down)
        elif finger_states == [True, False, False, False, False] and thumb_tip.y > landmarks[2].y:
            return HandGesture.BRIGHTNESS_DOWN
        
        return HandGesture.NONE

    def smooth_cursor_movement(self, x, y):
        """Apply smoothing to cursor movement for stability"""
        self.cursor_history.append((x, y))
        
        if len(self.cursor_history) < 2:
            return x, y
        
        # Weighted average with recent positions having more influence
        weights = np.linspace(0.1, 1.0, len(self.cursor_history))
        weights /= weights.sum()
        
        smooth_x = sum(pos[0] * weight for pos, weight in zip(self.cursor_history, weights))
        smooth_y = sum(pos[1] * weight for pos, weight in zip(self.cursor_history, weights))
        
        return int(smooth_x), int(smooth_y)

    def control_cursor(self, landmarks, frame_shape):
        """Control cursor movement with improved accuracy"""
        index_tip = landmarks[8]
        
        # Convert normalized coordinates to screen coordinates
        frame_height, frame_width = frame_shape[:2]
        
        # Apply calibration zone
        x_normalized = (index_tip.x - self.calibration_zone['x_min']) / \
                      (self.calibration_zone['x_max'] - self.calibration_zone['x_min'])
        y_normalized = (index_tip.y - self.calibration_zone['y_min']) / \
                      (self.calibration_zone['y_max'] - self.calibration_zone['y_min'])
        
        # Clamp values
        x_normalized = max(0, min(1, x_normalized))
        y_normalized = max(0, min(1, y_normalized))
        
        # Map to screen coordinates
        screen_x = int(x_normalized * self.screen_width)
        screen_y = int(y_normalized * self.screen_height)
        
        # Apply smoothing
        smooth_x, smooth_y = self.smooth_cursor_movement(screen_x, screen_y)
        
        # Move cursor
        pyautogui.moveTo(smooth_x, smooth_y)

    def execute_gesture(self, gesture):
        """Execute system commands based on recognized gesture"""
        current_time = time.time()
        
        # Prevent rapid gesture execution
        if current_time - self.last_gesture_time < self.gesture_delay:
            return
        
        try:
            if gesture == HandGesture.LEFT_CLICK:
                pyautogui.click()
                self.last_gesture_display = "Left Click"
                
            elif gesture == HandGesture.RIGHT_CLICK:
                pyautogui.rightClick()
                self.last_gesture_display = "Right Click"
                
            elif gesture == HandGesture.SCROLL_UP:
                pyautogui.scroll(self.scroll_sensitivity)
                self.last_gesture_display = "Scroll Up"
                
            elif gesture == HandGesture.SCROLL_DOWN:
                pyautogui.scroll(-self.scroll_sensitivity)
                self.last_gesture_display = "Scroll Down"
                
            elif gesture == HandGesture.VOLUME_UP:
                pyautogui.press('volumeup')
                self.last_gesture_display = "Volume Up"
                
            elif gesture == HandGesture.VOLUME_DOWN:
                pyautogui.press('volumedown')
                self.last_gesture_display = "Volume Down"
                
            elif gesture == HandGesture.BRIGHTNESS_UP:
                pyautogui.press('brightnessup')
                self.last_gesture_display = "Brightness Up"
                
            elif gesture == HandGesture.BRIGHTNESS_DOWN:
                pyautogui.press('brightnessdown')
                self.last_gesture_display = "Brightness Down"
                
            elif gesture == HandGesture.PLAY_PAUSE:
                pyautogui.press('playpause')
                self.last_gesture_display = "Play/Pause"
                
            elif gesture == HandGesture.NEXT_TRACK:
                pyautogui.press('nexttrack')
                self.last_gesture_display = "Next Track"
                
            elif gesture == HandGesture.PREV_TRACK:
                pyautogui.press('prevtrack')
                self.last_gesture_display = "Previous Track"
            
            if gesture != HandGesture.CURSOR_CONTROL:
                self.last_gesture_time = current_time
                self.gesture_display_start = current_time
                
        except Exception as e:
            print(f"Error executing gesture: {e}")

    def draw_landmarks_and_info(self, frame, landmarks, gesture):
        """Draw hand landmarks and system information on frame"""
        # Draw hand landmarks
        self.mp_draw.draw_landmarks(
            frame, landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2),
            self.mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)
        )
        
        # Draw calibration zone
        height, width = frame.shape[:2]
        x1 = int(self.calibration_zone['x_min'] * width)
        y1 = int(self.calibration_zone['y_min'] * height)
        x2 = int(self.calibration_zone['x_max'] * width)
        y2 = int(self.calibration_zone['y_max'] * height)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        
        # Draw gesture information
        current_time = time.time()
        if current_time - self.gesture_display_start < self.gesture_display_time:
            cv2.putText(frame, f"Action: {self.last_gesture_display}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw current gesture
        cv2.putText(frame, f"Gesture: {gesture.value}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw FPS
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}", 
                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw finger states with more detail
        finger_states = self.get_finger_states(landmarks.landmark)
        finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
        y_offset = 150
        
        cv2.putText(frame, "Finger States:", (width - 200, y_offset - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        for i, (name, state) in enumerate(zip(finger_names, finger_states)):
            color = (0, 255, 0) if state else (0, 0, 255)
            status = 'UP' if state else 'DOWN'
            cv2.putText(frame, f"{name}: {status}", 
                       (width - 200, y_offset + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Show total fingers up
        total_up = sum(finger_states)
        cv2.putText(frame, f"Total Up: {total_up}", 
                   (width - 200, y_offset + 5 * 25 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    def calculate_fps(self):
        """Calculate and update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time

    def run(self):
        """Main control loop"""
        print("Starting Hand Mouse Controller...")
        print("Show your hand to the camera to begin control")
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process frame
                results = self.hands.process(frame_rgb)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Recognize gesture
                        gesture = self.recognize_gesture(hand_landmarks.landmark)
                        
                        # Control cursor for appropriate gestures
                        if gesture in [HandGesture.CURSOR_CONTROL, HandGesture.LEFT_CLICK, HandGesture.RIGHT_CLICK]:
                            self.control_cursor(hand_landmarks.landmark, frame.shape)
                        
                        # Execute gesture
                        if gesture != HandGesture.NONE:
                            self.execute_gesture(gesture)
                        
                        # Draw landmarks and information
                        self.draw_landmarks_and_info(frame, hand_landmarks, gesture)
                
                else:
                    # No hand detected
                    cv2.putText(frame, "No hand detected - Show your hand to the camera", 
                               (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Display frame
                cv2.imshow("Professional Hand Mouse Controller", frame)
                
                # Exit condition
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):  # Calibrate
                    print("Calibration mode - Move your hand to corners of the screen")
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        print("Hand Mouse Controller stopped successfully!")

def main():
    """Main function to run the hand mouse controller"""
    controller = HandMouseController()
    controller.run()

if __name__ == "__main__":
    main()