import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import socket

# WiFi UDP connection 
UDP_IP = "IP_ADDRESS" # Replace with the IP address of the receiving device
UDP_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_udp_message(message):
    sock.sendto(bytes(message, "utf-8"), (UDP_IP, UDP_PORT))

last_sent_state = None

camera = 0

# Camera connection helper
def connect_camera(index):
    while True:
        print("Trying to connect camera...")

        cap = cv2.VideoCapture(index)

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            success, _ = cap.read()

            if success:
                print("Camera connected.")
                return cap

        print("Camera not available. Retrying in 1 second...")
        cap.release()
        time.sleep(1)

debug_mode = True  # Set to True to enable debug visuals, False for normal operation

# Gesture variables
GESTURE_SEQUENCE = ["Open_Palm", "Closed_Fist", "Victory", "Thumb_Up"] # Define the expected gesture sequence for access
GESTURE_DELAY = 0.5  # seconds
SUCCESS_COOLDOWN = 5  # seconds

last_gesture_time = 0
last_success_time = 0

# Initialize gesture
gesture_name = "None"
gesture_conf= 0.0

# Face variables
face_detected = False
face_conf = 0.0

# Global variables to store the latest results from callbacks
current_step = 0
last_detected_gesture = None

# Initialize MediaPipe
Face_BaseOptions = python.BaseOptions
Face_Detector = vision.FaceDetector
Face_DetectorOptions = vision.FaceDetectorOptions
Face_VisionRunningMode = vision.RunningMode

Gesture_BaseOptions = python.BaseOptions
Gesture_Recognizer = vision.GestureRecognizer
Gesture_RecognizerOptions = vision.GestureRecognizerOptions
Gesture_VisionRunningMode = vision.RunningMode

face_options = Face_DetectorOptions(
    base_options=Face_BaseOptions(model_asset_path="blaze_face_short_range.tflite"),
    running_mode=Face_VisionRunningMode.VIDEO
)

gesture_options = Gesture_RecognizerOptions(
    base_options=Gesture_BaseOptions(model_asset_path="gesture_recognizer.task"),
    running_mode=Gesture_VisionRunningMode.VIDEO,
    num_hands=1
)

face_detector = Face_Detector.create_from_options(face_options)
gesture_recognizer = Gesture_Recognizer.create_from_options(gesture_options)

cap = connect_camera(camera)

cv2.namedWindow('Biometric Pass System', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Biometric Pass System', 640, 480)

while cap.isOpened():
    success, frame = cap.read()
    
    if not success:
        print("Camera disconnected.")
        
        current_state = 'E' # Camera connection error
        if current_state != last_sent_state:
            send_udp_message(current_state)
            last_sent_state = current_state
        
        cap.release()

        cap = connect_camera(camera)
        continue

    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    timestamp_ms = int(time.time() * 1000)
    face_result = face_detector.detect_for_video(mp_image, timestamp_ms)
    gesture_result = gesture_recognizer.recognize_for_video(mp_image, timestamp_ms)

    if face_result.detections:
        detection = face_result.detections[0]
        face_conf = round(detection.categories[0].score, 2)
        
        if face_conf > 0.75:
            face_detected = True
            bbox = detection.bounding_box
            x_min = int(bbox.origin_x)
            y_min = int(bbox.origin_y)
            box_width = int(bbox.width)
            box_height = int(bbox.height)
        else:
            face_detected = False
    else:
        face_detected = False

    if face_detected:
        current_state = 'F'  # Face detected
    else:
        current_state = 'N'  # No face detected

    current_time = time.time()

    if (current_time - last_success_time) < SUCCESS_COOLDOWN:
        gesture_name = "None"
        gesture_conf = 0.0

        if debug_mode:
            cv2.putText(frame, 
                        "COOLDOWN", 
                        (360, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.8, (0, 0, 255), 2)

    elif not gesture_result.gestures:
        gesture_name = "None"
        gesture_conf = 0.0

        if debug_mode:
            cv2.putText(frame, 
                        "NO HAND DETECTED", 
                        (360, 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.8, (255, 0, 0), 2)
            
    elif gesture_result.gestures:
        gesture = gesture_result.gestures[0][0]
        gesture_name = gesture.category_name
        gesture_conf = round(gesture.score, 2)

        if gesture_name == "None":
            last_detected_gesture = None

        elif face_detected and gesture_conf > 0.5:
                    
            if gesture_name != last_detected_gesture and (current_time - last_gesture_time) > GESTURE_DELAY:
                        
                if gesture_name == GESTURE_SEQUENCE[current_step]:
                    current_step += 1
                    
                    if debug_mode:
                        print(f"Step {current_step} Correct: {gesture_name}")
                            

                    if current_step == len(GESTURE_SEQUENCE):
                        current_state = 'C'
                        current_step = 0 # Reset for next attempt
                        last_success_time = time.time()

                        if debug_mode:
                            print("SUCCESS: Access Granted!")
                        
                        
                else:
                    current_state = 'W'
                    current_step = 0

                    if debug_mode:
                        print(f"WRONG GESTURE: {gesture_name} - Expected: {GESTURE_SEQUENCE[current_step]}. Resetting the sequence.")
                    
                last_gesture_time = current_time
                last_detected_gesture = gesture_name
                    
        else:
            # If no hand is detected, clear last_detected_gesture 
            last_detected_gesture = None

    else:
        last_detected_gesture = None

    if current_state != last_sent_state:
            send_udp_message(current_state)
            last_sent_state = current_state
            
    if debug_mode:           
        cv2.putText(frame, f'Gesture: {gesture_name} ({gesture_conf})', 
                            (10, 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.8, (0, 255, 0), 2, 
                            cv2.LINE_AA)
                    
        cv2.putText(frame, f"Step: {current_step}/{len(GESTURE_SEQUENCE)}", 
                            (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.8, (255, 0, 0), 2)
        
        if face_detected:
            cv2.rectangle(frame, 
                          (x_min, y_min), (x_min + box_width, y_min + box_height), 
                          (0, 255, 0), 2)
                
            cv2.putText(frame, 
                        f"Confidence: {int(detection.categories[0].score * 100)}%", 
                        (x_min, y_min - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (0, 255, 0), 2)
        
        else:
            cv2.putText(frame, 
                        "FACE NOT DETECTED", 
                        (10, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.8, (0, 0, 255), 2)
                
    cv2.imshow('Biometric Pass System', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        send_udp_message('Q')
        break

cap.release()
cv2.destroyAllWindows()
face_detector.close()
