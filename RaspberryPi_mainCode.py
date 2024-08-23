from typing import Union
import requests
from enum import Enum
import RPi.GPIO as GPIO
import time
import cv2
import mediapipe as mp

# Define DJI control client (replace with your IP and port) !!!
client = DJIControlClient("IP", PORT)  

takeoff_led = 20
seeed_studio_tx = 16
button_rotate_right = 5
face_control_led = 25
button_up = 9
button_rotate_left = 10
button_fly_right = 17
seeed_studio_rx = 15
voice_control_led = 14
fly_forward = 4
fly_left = 3
fly_back = 2
estop_button = GPIO.BOARD  

voice_commands = {
    "stop!": "stop",
    "drone up": "move_up",
    "drone down": "move_down",
    "drone left": "move_left",
    "drone right": "move_right",
    "drone rotate left": "rotate_left",
    "drone rotate right": "rotate_right",
    "face control on": "face_control_on",
    "face control off": "face_control_off",
    "takeoff": "takeoff",
    "land": "land",
    "come home": "land",  
    "Face mode": "face_control_on",
    "Button mode": "button_control_on",
    "Voice mode": "voice_control_on",
}

movement_speed = 0.5  

current_control_mode = "stop"  

def set_led(led_pin, state):
    GPIO.output(led_pin, state)

def change_mode_lights(new_mode):
    if new_mode == "face_control_on":
        set_led(face_control_led, 1)
        set_led(voice_control_led, 0)
    elif new_mode == "button_control_on":
        set_led(face_control_led, 0)
        set_led(voice_control_led, 1)
    else:
        set_led(face_control_led, 0)
        set_led(voice_control_led, 0)

def button_control():
    global current_control_mode

    if GPIO.input(button_up) == 0:
        client.moveUp(0.1)  
    if GPIO.input(button_down) == 0:
        client.moveDown(0.1)  
    if GPIO.input(button_rotate_left) == 0:
        client.rotateCounterClockwise(10)  
    if GPIO.input(button_rotate_right) == 0:
        client.rotateClockwise(10)  
    if GPIO.input(button_fly_right) == 0:
        client.moveRight(0.1)  
    if GPIO.input(fly_forward) == 0:
        client.moveForward(0.1)  
    if GPIO.input(fly_left) == 0:
        client.moveLeft(0.1)  
    if GPIO.input(fly_back) == 0:
        client.moveBackward(0.1)  
    current_control_mode = "button_control"

def face_control():
    global current_control_mode

    mp_drawing = mp.solutions.drawing_utils
    mp_face_detection = mp.solutions.face_detection
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_face_mesh = mp.solutions.face_mesh

    cap = cv2.VideoCapture(0)

    with mp_face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5) as face_detection, mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as face_mesh:
        while True:
            success, image = cap.read()

            results = face_detection.process(image)

            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    x, y, w, h = int(bbox.xmin * image.shape[1]), int(bbox.ymin * image.shape[0]), int(bbox.width * image.shape[1]), int(bbox.height * image.shape[0])

                    face_center_x = x + w // 2
                    face_center_y = y + h // 2

                    angle = (face_center_x - image.shape[1] // 2) / (image.shape[1] // 2) * 90

                    if angle > 10:
                        client.rotateClockwise(angle)
                    elif angle < -10:
                        client.rotateCounterClockwise(-angle)

                    if face_center_y < image.shape[0] // 3:
                        client.moveUp(0.1)
                    elif face_center_y > image.shape[0] // 3 * 2:
                        client.moveDown(0.1)

                    results = face_mesh.process(image)

                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            mouth_landmarks = face_landmarks[48:60]

                            mouth_opening = calculate_mouth_opening(mouth_landmarks)

                            if mouth_opening > 0.2:
                                client.moveForward(0.1)

            cv2.imshow('Face Detection', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

def calculate_mouth_opening(mouth_landmarks):
    mouth_upper_lip_top = mouth_landmarks[10]
    mouth_upper_lip_bottom = mouth_landmarks[14]
    mouth_lower_lip_top = mouth_landmarks[18]
    mouth_lower_lip_bottom = mouth_landmarks[26]

    distance_vertical = mouth_upper_lip_top.y - mouth_lower_lip_bottom.y
    distance_horizontal = mouth_upper_lip_top.x - mouth_lower_lip_bottom.x
    mouth_opening = distance_vertical / distance_horizontal

    return mouth_opening

def main():
    global current_control_mode

    while True:
        handle_estop()

        change_mode_lights(current_control_mode)

        command = listen_for_command()
        if command is not None:
            if command in voice_commands:
                execute_command(voice_commands[command])

        if current_control_mode == "button_control":
            button_control()

        if current_control_mode == "face_control_on":
            face_control()

if __name__ == "__main__":
    main()
