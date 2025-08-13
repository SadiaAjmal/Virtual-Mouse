import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
from collections import deque

# Disable pyautogui failsafe for smoother operation
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Initialize webcam and face mesh
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Get screen dimensions
screen_w, screen_h = pyautogui.size()

# Smoothing for cursor movement
SMOOTHING_WINDOW = 5
x_history = deque(maxlen=SMOOTHING_WINDOW)
y_history = deque(maxlen=SMOOTHING_WINDOW)

# Eye control variables
left_eye_values = []
right_eye_values = []
is_calibrating = True
calibration_frames = 0
CALIBRATION_DURATION = 120

# Enhanced calibration for eye boundaries
eye_x_positions = []
eye_y_positions = []
min_eye_x, max_eye_x = float('inf'), float('-inf')
min_eye_y, max_eye_y = float('inf'), float('-inf')

# Wink thresholds (will be set after calibration)
left_wink_threshold = 0.02
right_wink_threshold = 0.02
normal_left_ear = 0.04
normal_right_ear = 0.04

# IMPROVED CLICK CONTROL
last_action_time = 0
MIN_ACTION_INTERVAL = 0.6  # REDUCED from 0.8 to 0.6 seconds for better response
left_wink_detected = False
right_wink_detected = False

# WINK CONFIRMATION SYSTEM - REDUCED FOR BETTER RESPONSE
left_wink_frames = 0
right_wink_frames = 0
WINK_CONFIRMATION_FRAMES = 2  # Reduced from 3 to 2 frames for faster response

# Double click with quick successive winks
last_right_wink_time = 0
DOUBLE_WINK_WINDOW = 0.7
wink_count = 0

# Screen mapping parameters
EDGE_EXPANSION = 0.15  # 15% expansion beyond detected range
screen_mapping_ready = False

def map_eye_to_screen(eye_x, eye_y):
    """Enhanced mapping function with proper boundary handling"""
    global min_eye_x, max_eye_x, min_eye_y, max_eye_y
    
    if not screen_mapping_ready:
        return int(eye_x * screen_w), int(eye_y * screen_h)
    
    # Expand the eye range by EDGE_EXPANSION to ensure full screen coverage
    eye_range_x = max_eye_x - min_eye_x
    eye_range_y = max_eye_y - min_eye_y
    
    expanded_min_x = min_eye_x - (eye_range_x * EDGE_EXPANSION)
    expanded_max_x = max_eye_x + (eye_range_x * EDGE_EXPANSION)
    expanded_min_y = min_eye_y - (eye_range_y * EDGE_EXPANSION)
    expanded_max_y = max_eye_y + (eye_range_y * EDGE_EXPANSION)
    
    # Normalize eye position to 0-1 range with expanded boundaries
    if expanded_max_x > expanded_min_x:
        norm_x = (eye_x - expanded_min_x) / (expanded_max_x - expanded_min_x)
    else:
        norm_x = 0.5
        
    if expanded_max_y > expanded_min_y:
        norm_y = (eye_y - expanded_min_y) / (expanded_max_y - expanded_min_y)
    else:
        norm_y = 0.5
    
    # Clamp to 0-1 range and map to screen
    norm_x = max(0, min(1, norm_x))
    norm_y = max(0, min(1, norm_y))
    
    screen_x = int(norm_x * screen_w)
    screen_y = int(norm_y * screen_h)
    
    # Ensure cursor stays within screen bounds
    screen_x = max(0, min(screen_w - 1, screen_x))
    screen_y = max(0, min(screen_h - 1, screen_y))
    
    return screen_x, screen_y

print("=== ENHANCED EYE MOUSE CONTROL - FIXED VERSION ===")
print("IMPROVED - Better accuracy, no accidental clicks!")
print("1. Look around during calibration (including corners)")
print("2. Try gentle left and right winks")
print("")
print("CONTROLS (after calibration):")
print("- LOOK AROUND = Move cursor (full screen coverage)")
print("- LEFT WINK = Single click")
print("- RIGHT WINK = Right click")
print("- RIGHT WINK TWICE (quick) = Double click")
print("")
print("Tips: Look to all corners during calibration!")
print("Press ESC to exit")

while True:
    ret, frame = cam.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    output = face_mesh.process(rgb_frame)
    landmark_points = output.multi_face_landmarks
    frame_h, frame_w, _ = frame.shape
    
    if landmark_points:
        landmarks = landmark_points[0].landmark
        
        # === ENHANCED CURSOR MOVEMENT ===
        right_iris = landmarks[474]
        left_iris = landmarks[469]
        
        # Use both eyes for smoother cursor movement
        avg_x = (right_iris.x + left_iris.x) / 2
        avg_y = (right_iris.y + left_iris.y) / 2
        
        # Track eye position boundaries during calibration
        if is_calibrating:
            eye_x_positions.append(avg_x)
            eye_y_positions.append(avg_y)
            min_eye_x = min(min_eye_x, avg_x)
            max_eye_x = max(max_eye_x, avg_x)
            min_eye_y = min(min_eye_y, avg_y)
            max_eye_y = max(max_eye_y, avg_y)
        
        # Map eye position to screen coordinates
        screen_x, screen_y = map_eye_to_screen(avg_x, avg_y)
        
        x_history.append(screen_x)
        y_history.append(screen_y)
        
        if len(x_history) >= 3:
            smooth_x = int(np.mean(x_history))
            smooth_y = int(np.mean(y_history))
            
            if not is_calibrating:
                pyautogui.moveTo(smooth_x, smooth_y, duration=0.1)  # Increased from 0.02 to 0.1 sec for slower movement
        
        # === WINK DETECTION ===
        # Left eye landmarks
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        left_eye_left = landmarks[33]
        left_eye_right = landmarks[133]
        
        # Right eye landmarks
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]
        right_eye_left = landmarks[362]
        right_eye_right = landmarks[263]
        
        # Calculate EAR for each eye separately
        left_vertical = abs(left_eye_top.y - left_eye_bottom.y)
        left_horizontal = abs(left_eye_left.x - left_eye_right.x)
        left_ear = left_vertical / (left_horizontal + 1e-6)
        
        right_vertical = abs(right_eye_top.y - right_eye_bottom.y)
        right_horizontal = abs(right_eye_left.x - right_eye_right.x)
        right_ear = right_vertical / (right_horizontal + 1e-6)
        
        # === ENHANCED CALIBRATION PHASE ===
        if is_calibrating:
            left_eye_values.append(left_ear)
            right_eye_values.append(right_ear)
            calibration_frames += 1
            
            # Show calibration progress and instructions
            progress = int((calibration_frames / CALIBRATION_DURATION) * 100)
            cv2.putText(frame, f'CALIBRATING... {progress}%', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, 'Look around - especially corners!', 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, 'Try gentle winks too', 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Show current eye range detection
            range_x = max_eye_x - min_eye_x if max_eye_x > min_eye_x else 0
            range_y = max_eye_y - min_eye_y if max_eye_y > min_eye_y else 0
            cv2.putText(frame, f'Eye Range: X={range_x:.3f}, Y={range_y:.3f}', 
                       (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            if calibration_frames >= CALIBRATION_DURATION:
                # Calculate wink thresholds - MORE CONSERVATIVE
                normal_left_ear = np.mean(left_eye_values)
                normal_right_ear = np.mean(right_eye_values)
                left_std = np.std(left_eye_values)
                right_std = np.std(right_eye_values)
                
                # IMPROVED: Less strict thresholds for better responsiveness
                left_wink_threshold = normal_left_ear - (1.8 * left_std)  # Changed from 2.0 to 1.8
                right_wink_threshold = normal_right_ear - (1.8 * right_std)  # Changed from 2.0 to 1.8
                
                # Finalize screen mapping
                screen_mapping_ready = True
                is_calibrating = False
                
                print(f"Enhanced calibration complete!")
                print(f"Eye tracking range - X: {min_eye_x:.4f} to {max_eye_x:.4f}")
                print(f"Eye tracking range - Y: {min_eye_y:.4f} to {max_eye_y:.4f}")
                print(f"Left eye normal: {normal_left_ear:.4f}, wink threshold: {left_wink_threshold:.4f}")
                print(f"Right eye normal: {normal_right_ear:.4f}, wink threshold: {right_wink_threshold:.4f}")
                print("Ready! Full screen coverage enabled with improved accuracy.")
        
        # === IMPROVED WINK DETECTION (after calibration) ===
        else:
            current_time = time.time()
            
            # IMPROVED: Balanced wink detection - responsive but accurate
            left_winking = (left_ear < left_wink_threshold and 
                           right_ear > (normal_right_ear * 0.82) and  # Reduced from 0.85 to 0.82
                           left_ear < (normal_left_ear * 0.65))  # Relaxed from 0.6 to 0.65
            
            right_winking = (right_ear < right_wink_threshold and 
                            left_ear > (normal_left_ear * 0.82) and  # Reduced from 0.85 to 0.82
                            right_ear < (normal_right_ear * 0.65))  # Relaxed from 0.6 to 0.65
            
            # IMPROVED: Wink confirmation system
            # Left wink confirmation and action
            if left_winking:
                left_wink_frames += 1
            else:
                left_wink_frames = 0
                left_wink_detected = False
            
            # Only click after confirmed wink
            if (left_wink_frames >= WINK_CONFIRMATION_FRAMES and 
                not left_wink_detected and 
                current_time - last_action_time > MIN_ACTION_INTERVAL):
                pyautogui.click()
                print("LEFT WINK - CLICK!")
                last_action_time = current_time
                left_wink_detected = True
                cv2.putText(frame, 'LEFT CLICK!', (10, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            
            # Right wink confirmation and action
            if right_winking:
                right_wink_frames += 1
            else:
                right_wink_frames = 0
                right_wink_detected = False
            
            # Only click after confirmed wink
            if (right_wink_frames >= WINK_CONFIRMATION_FRAMES and 
                not right_wink_detected and 
                current_time - last_action_time > MIN_ACTION_INTERVAL):
                
                # Check for double wink
                if (current_time - last_right_wink_time < DOUBLE_WINK_WINDOW and 
                    wink_count >= 1):
                    # Double click
                    pyautogui.doubleClick()
                    print("DOUBLE RIGHT WINK - DOUBLE CLICK!")
                    wink_count = 0
                    cv2.putText(frame, 'DOUBLE CLICK!', (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 3)
                else:
                    # Single right click
                    pyautogui.rightClick()
                    print("RIGHT WINK - RIGHT CLICK!")
                    wink_count += 1
                    last_right_wink_time = current_time
                    cv2.putText(frame, 'RIGHT CLICK!', (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
                
                last_action_time = current_time
                right_wink_detected = True
            
            # Reset double wink counter after timeout
            if current_time - last_right_wink_time > DOUBLE_WINK_WINDOW:
                wink_count = 0
            
            # Display enhanced status
            cv2.putText(frame, f'Cursor: ({smooth_x}, {smooth_y})', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f'Eye Pos: ({avg_x:.3f}, {avg_y:.3f})', (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2)
            cv2.putText(frame, f'Left Eye: {left_ear:.4f} ({left_wink_frames})', (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, f'Right Eye: {right_ear:.4f} ({right_wink_frames})', (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Show wink status with confirmation
            if left_wink_frames > 0:
                cv2.putText(frame, f'LEFT WINKING! ({left_wink_frames}/{WINK_CONFIRMATION_FRAMES})', (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            if right_wink_frames > 0:
                cv2.putText(frame, f'RIGHT WINKING! ({right_wink_frames}/{WINK_CONFIRMATION_FRAMES})', (250, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Show double wink countdown
            if wink_count > 0:
                remaining = DOUBLE_WINK_WINDOW - (current_time - last_right_wink_time)
                if remaining > 0:
                    cv2.putText(frame, f'Double wink: {remaining:.1f}s', (10, 180), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw eye landmarks with different colors
        # Left eye (green)
        left_landmarks = [33, 133, 159, 145, 469]
        for landmark_id in left_landmarks:
            landmark = landmarks[landmark_id]
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        
        # Right eye (red)
        right_landmarks = [362, 263, 386, 374, 474]
        for landmark_id in right_landmarks:
            landmark = landmarks[landmark_id]
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)
    
    else:
        cv2.putText(frame, 'No face detected!', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
    
    cv2.imshow('Enhanced Eye Mouse - Fixed Version', frame)
    
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cam.release()
cv2.destroyAllWindows()
pyautogui.FAILSAFE = True