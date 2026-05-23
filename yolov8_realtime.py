import cv2
import requests 
from ultralytics import YOLO
import time

def run_realtime_detection():
    # Load the YOLOv8 Nano model (pretrained)
    # This will automatically download the 'yolov8n.pt' file if it's not and doesn't exist
    print("Loading YOLOv8 model...")
    model = YOLO('yolov8n.pt')
    
    # Initialize webcam
    # 0 is usually the default camera. Change to 1, 2, etc. if you have multiple cameras.
    print("Initializing webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Detection started. Press 'q' to quit.")
    
    # Window setup
    cv2.namedWindow('YOLOv8 Real-Time Detection', cv2.WINDOW_NORMAL)
    
    prev_time = 0
    
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Could not read frame from webcam.")
            break
            
        # Run YOLOv8 inference on the frame
        # stream=True for memory efficiency when processing video
        results = model(frame, stream=True)
        
        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time
        
        # Process results and visualize
        for r in results:
            annotated_frame = r.plot()  # r.plot() returns a numpy array with boxes/labels

            # Extract detected objects with positions
            detected_objects = {}
            if r.boxes is not None and hasattr(r.boxes, 'cls') and hasattr(r.boxes, 'xyxy'):
                for cls_id, box in zip(r.boxes.cls, r.boxes.xyxy):
                    # Convert class index to label name using model.names
                    if hasattr(model, 'names'):
                        label = model.names[int(cls_id)]
                    else:
                        label = str(int(cls_id))
                    # box: [x1, y1, x2, y2] (top-left and bottom-right)
                    x1, y1, x2, y2 = box.tolist()
                    # Calculate center position
                    x = int((x1 + x2) / 2)
                    y = int((y1 + y2) / 2)
                    detected_objects[label] = {"position": {"x": x, "y": y}}

            # Draw FPS on frame
            cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Send detected objects and positions to server in mapped format
            requests.post(
                "http://127.0.0.1:8095/sensory_message",
                json={
                    "Object_detection_1": detected_objects
                }
            )
            # Show the frame
            cv2.imshow('YOLOv8 Real-Time Detection', annotated_frame)
            
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Detection stopped.")

if __name__ == "__main__":
    run_realtime_detection()
