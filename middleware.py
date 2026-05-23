import serial
import serial.tools.list_ports
import cv2
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Microcontroller Serial Ports (Assume automatically detected)
STM32F401RET6_port = None
STM32G473RCT6_port = None


# Serial Device instances (populated in initialization)
QUECTEL_EC25_serial = None
Intel_Realsense_RPLIDAR_A2_serial = None


# Camera/Vision System instances
IMX179_camera = None
FLIR_Duo_Pro_R_camera = None
USB_camera_5MPX_camera = None
Fish_eye_lens_camera = None


# Camera device category
camera_devices = {
    'IMX179_8MP_USB_Camera.glb': 'Vision_system',
    'FLIR_Duo_Pro_R.glb': 'Vision_system',
    'USB_camera_5MPX.glb': 'Vision_system',
    'Fish_eye_lens_camera.gltf': 'Vision_system'
}

# Communication device category
communication_devices = {
    'QUECTEL_EC25_v3.glb': 'Communication_system'
}

# Sensor device category
sensor_devices = {
    'Intel_Realsense_RPLIDAR_A2.glb': 'Sensors'
}



# Function to detect available camera indices
def detect_cameras():
    """Detects available camera indices using OpenCV."""
    available_cameras = []
    for i in range(10):  # Check indices 0 to 9 (adjust range as needed)
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras


# Generic serial port configuration.  Modify as needed for each device.
SERIAL_CONFIG = {
    'baudrate': 115200,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': 1
}


def initialize_serial_ports():
    """Initializes serial ports for microcontrollers and serial devices."""
    global STM32F401RET6_port, STM32G473RCT6_port
    global QUECTEL_EC25_serial, Intel_Realsense_RPLIDAR_A2_serial

    # Find Serial Ports
    ports = list(serial.tools.list_ports.comports())
    logging.info(f"Available serial ports: {ports}")


    # Placeholder for finding microcontrollers by VID/PID or similar unique identifier
    # This is just a stub.  You NEED to replace this with your specific detection logic.
    for port, desc, hwid in sorted(ports):
        if "STM32" in desc:  # Example, adjust based on actual description
            if STM32F401RET6_port is None:
                 STM32F401RET6_port = port
                 logging.info(f"Detected STM32F401RET6 on port: {port}")
            elif STM32G473RCT6_port is None:
                STM32G473RCT6_port = port
                logging.info(f"Detected STM32G473RCT6 on port: {port}")

        if "Quectel" in desc: # Example, adjust based on actual description
            try:
                QUECTEL_EC25_serial = serial.Serial(port, **SERIAL_CONFIG)
                logging.info(f"Detected QUECTEL_EC25 on port: {port}")
            except serial.SerialException as e:
                logging.error(f"Error opening QUECTEL_EC25 serial port: {e}")

        if "RPLIDAR" in desc: # Example, adjust based on actual description
            try:
                Intel_Realsense_RPLIDAR_A2_serial = serial.Serial(port, **SERIAL_CONFIG)
                logging.info(f"Detected Intel_Realsense_RPLIDAR_A2 on port: {port}")
            except serial.SerialException as e:
                logging.error(f"Error opening Intel_Realsense_RPLIDAR_A2 serial port: {e}")


    if STM32F401RET6_port is None:
        logging.warning("STM32F401RET6 not detected.")

    if STM32G473RCT6_port is None:
        logging.warning("STM32G473RCT6 not detected.")

    if QUECTEL_EC25_serial is None:
        logging.warning("QUECTEL_EC25 not detected.")

    if Intel_Realsense_RPLIDAR_A2_serial is None:
        logging.warning("Intel_Realsense_RPLIDAR_A2 not detected.")



def initialize_cameras():
    """Initializes the camera/vision systems using OpenCV."""
    global IMX179_camera, FLIR_Duo_Pro_R_camera, USB_camera_5MPX_camera, Fish_eye_lens_camera

    available_camera_indices = detect_cameras()
    logging.info(f"Available camera indices: {available_camera_indices}")

    if not available_camera_indices:
        logging.warning("No cameras detected.")
        return

    # Initialize cameras.  Assign camera indices based on detection.
    # WARNING:  The order of detection may not be consistent.
    # You'll likely need to implement more sophisticated detection logic
    # using camera properties (e.g., name, serial number) to reliably
    # assign the correct camera index to each global camera variable.

    camera_index = 0 # start with index 0
    if 'IMX179_8MP_USB_Camera.glb' in camera_devices and camera_index < len(available_camera_indices):
         IMX179_camera = cv2.VideoCapture(available_camera_indices[camera_index])
         if IMX179_camera.isOpened():
              logging.info(f"IMX179_camera initialized on index: {available_camera_indices[camera_index]}")
         else:
             logging.warning(f"Failed to initialize IMX179_camera on index: {available_camera_indices[camera_index]}")
         camera_index+=1


    if 'FLIR_Duo_Pro_R.glb' in camera_devices and camera_index < len(available_camera_indices):
        FLIR_Duo_Pro_R_camera = cv2.VideoCapture(available_camera_indices[camera_index])
        if FLIR_Duo_Pro_R_camera.isOpened():
            logging.info(f"FLIR_Duo_Pro_R_camera initialized on index: {available_camera_indices[camera_index]}")
        else:
            logging.warning(f"Failed to initialize FLIR_Duo_Pro_R_camera on index: {available_camera_indices[camera_index]}")
        camera_index += 1

    if 'USB_camera_5MPX.glb' in camera_devices and camera_index < len(available_camera_indices):
        USB_camera_5MPX_camera = cv2.VideoCapture(available_camera_indices[camera_index])
        if USB_camera_5MPX_camera.isOpened():
            logging.info(f"USB_camera_5MPX_camera initialized on index: {available_camera_indices[camera_index]}")
        else:
            logging.warning(f"Failed to initialize USB_camera_5MPX_camera on index: {available_camera_indices[camera_index]}")
        camera_index += 1


    if 'Fish_eye_lens_camera.gltf' in camera_devices and camera_index < len(available_camera_indices):
        Fish_eye_lens_camera = cv2.VideoCapture(available_camera_indices[camera_index])
        if Fish_eye_lens_camera.isOpened():
            logging.info(f"Fish_eye_lens_camera initialized on index: {available_camera_indices[camera_index]}")
        else:
            logging.warning(f"Failed to initialize Fish_eye_lens_camera on index: {available_camera_indices[camera_index]}")
        camera_index += 1



def read_stm32f401ret6():
    """Reads data from STM32F401RET6."""
    if STM32F401RET6_port:
        try:
            with serial.Serial(STM32F401RET6_port, **SERIAL_CONFIG) as ser:
                # Add your reading logic here
                data = ser.readline().decode('utf-8').strip()
                return data
        except serial.SerialException as e:
            logging.error(f"Error reading from STM32F401RET6: {e}")
            return None
    else:
        logging.warning("STM32F401RET6 port not initialized.")
        return None


def write_stm32f401ret6(data):
    """Writes data to STM32F401RET6."""
    if STM32F401RET6_port:
        try:
            with serial.Serial(STM32F401RET6_port, **SERIAL_CONFIG) as ser:
                ser.write(data.encode('utf-8'))
        except serial.SerialException as e:
            logging.error(f"Error writing to STM32F401RET6: {e}")
    else:
        logging.warning("STM32F401RET6 port not initialized.")



def read_stm32g473rct6():
    """Reads data from STM32G473RCT6."""
    if STM32G473RCT6_port:
        try:
            with serial.Serial(STM32G473RCT6_port, **SERIAL_CONFIG) as ser:
                # Add your reading logic here
                data = ser.readline().decode('utf-8').strip()
                return data
        except serial.SerialException as e:
            logging.error(f"Error reading from STM32G473RCT6: {e}")
            return None
    else:
        logging.warning("STM32G473RCT6 port not initialized.")
        return None


def write_stm32g473rct6(data):
    """Writes data to STM32G473RCT6."""
    if STM32G473RCT6_port:
        try:
            with serial.Serial(STM32G473RCT6_port, **SERIAL_CONFIG) as ser:
                ser.write(data.encode('utf-8'))
        except serial.SerialException as e:
            logging.error(f"Error writing to STM32G473RCT6: {e}")
    else:
        logging.warning("STM32G473RCT6 port not initialized.")


def read_quectel_ec25():
    """Reads data from QUECTEL_EC25."""
    if QUECTEL_EC25_serial and QUECTEL_EC25_serial.is_open:
        try:
            data = QUECTEL_EC25_serial.readline().decode('utf-8').strip()
            return data
        except serial.SerialException as e:
            logging.error(f"Error reading from QUECTEL_EC25: {e}")
            return None
    else:
        logging.warning("QUECTEL_EC25 serial not initialized or not open.")
        return None

def write_quectel_ec25(data):
    """Writes data to QUECTEL_EC25."""
    if QUECTEL_EC25_serial and QUECTEL_EC25_serial.is_open:
        try:
            QUECTEL_EC25_serial.write(data.encode('utf-8'))
        except serial.SerialException as e:
            logging.error(f"Error writing to QUECTEL_EC25: {e}")
    else:
        logging.warning("QUECTEL_EC25 serial not initialized or not open.")


def read_intel_realsense_rplidar_a2():
    """Reads data from Intel_Realsense_RPLIDAR_A2."""
    if Intel_Realsense_RPLIDAR_A2_serial and Intel_Realsense_RPLIDAR_A2_serial.is_open:
        try:
            data = Intel_Realsense_RPLIDAR_A2_serial.readline()  # Assuming binary data
            return data
        except serial.SerialException as e:
            logging.error(f"Error reading from Intel_Realsense_RPLIDAR_A2: {e}")
            return None
    else:
        logging.warning("Intel_Realsense_RPLIDAR_A2 serial not initialized or not open.")
        return None



def write_intel_realsense_rplidar_a2(data):
    """Writes data to Intel_Realsense_RPLIDAR_A2."""
    if Intel_Realsense_RPLIDAR_A2_serial and Intel_Realsense_RPLIDAR_A2_serial.is_open:
        try:
            Intel_Realsense_RPLIDAR_A2_serial.write(data) # Assuming binary data
        except serial.SerialException as e:
            logging.error(f"Error writing to Intel_Realsense_RPLIDAR_A2: {e}")
    else:
        logging.warning("Intel_Realsense_RPLIDAR_A2 serial not initialized or not open.")


def read_imx179_camera():
    """Reads a frame from IMX179_camera."""
    if IMX179_camera and IMX179_camera.isOpened():
        ret, frame = IMX179_camera.read()
        if not ret:
            logging.error("Failed to grab frame from IMX179_camera")
            return None
        return frame
    else:
        logging.warning("IMX179_camera not initialized or not open.")
        return None


def read_flir_duo_pro_r_camera():
    """Reads a frame from FLIR_Duo_Pro_R_camera."""
    if FLIR_Duo_Pro_R_camera and FLIR_Duo_Pro_R_camera.isOpened():
        ret, frame = FLIR_Duo_Pro_R_camera.read()
        if not ret:
            logging.error("Failed to grab frame from FLIR_Duo_Pro_R_camera")
            return None
        return frame
    else:
        logging.warning("FLIR_Duo_Pro_R_camera not initialized or not open.")
        return None



def read_usb_camera_5mpx_camera():
    """Reads a frame from USB_camera_5MPX_camera."""
    if USB_camera_5MPX_camera and USB_camera_5MPX_camera.isOpened():
        ret, frame = USB_camera_5MPX_camera.read()
        if not ret:
            logging.error("Failed to grab frame from USB_camera_5MPX_camera")
            return None
        return frame
    else:
        logging.warning("USB_camera_5MPX_camera not initialized or not open.")
        return None



def read_fish_eye_lens_camera():
    """Reads a frame from Fish_eye_lens_camera."""
    if Fish_eye_lens_camera and Fish_eye_lens_camera.isOpened():
        ret, frame = Fish_eye_lens_camera.read()
        if not ret:
            logging.error("Failed to grab frame from Fish_eye_lens_camera")
            return None
        return frame
    else:
        logging.warning("Fish_eye_lens_camera not initialized or not open.")
        return None


def close_all_cameras():
    """Releases all camera resources."""
    global IMX179_camera, FLIR_Duo_Pro_R_camera, USB_camera_5MPX_camera, Fish_eye_lens_camera

    if IMX179_camera and IMX179_camera.isOpened():
        IMX179_camera.release()
        logging.info("IMX179_camera released.")
    if FLIR_Duo_Pro_R_camera and FLIR_Duo_Pro_R_camera.isOpened():
        FLIR_Duo_Pro_R_camera.release()
        logging.info("FLIR_Duo_Pro_R_camera released.")
    if USB_camera_5MPX_camera and USB_camera_5MPX_camera.isOpened():
        USB_camera_5MPX_camera.release()
        logging.info("USB_camera_5MPX_camera released.")
    if Fish_eye_lens_camera and Fish_eye_lens_camera.isOpened():
        Fish_eye_lens_camera.release()
        logging.info("Fish_eye_lens_camera released.")



def initialize_all():
    """Initializes all serial ports and cameras."""
    initialize_serial_ports()
    initialize_cameras()


def cleanup_all():
    """Cleans up all resources."""
    close_all_cameras()
    if QUECTEL_EC25_serial and QUECTEL_EC25_serial.is_open:
        QUECTEL_EC25_serial.close()
        logging.info("QUECTEL_EC25 serial port closed.")
    if Intel_Realsense_RPLIDAR_A2_serial and Intel_Realsense_RPLIDAR_A2_serial.is_open:
        Intel_Realsense_RPLIDAR_A2_serial.close()
        logging.info("Intel_Realsense_RPLIDAR_A2 serial port closed.")




if __name__ == '__main__':
    initialize_all()

    try:
        # Example Usage:  Replace with your control logic.
        while True:
            # Read from STM32s
            stm32f401_data = read_stm32f401ret6()
            if stm32f401_data:
                logging.info(f"Received from STM32F401RET6: {stm32f401_data}")

            stm32g473_data = read_stm32g473rct6()
            if stm32g473_data:
                logging.info(f"Received from STM32G473RCT6: {stm32g473_data}")


            # Read from Quectel
            quectel_data = read_quectel_ec25()
            if quectel_data:
                logging.info(f"Received from QUECTEL_EC25: {quectel_data}")


            # Read from RPLIDAR
            rplidar_data = read_intel_realsense_rplidar_a2()
            if rplidar_data:
                logging.info(f"Received from Intel_Realsense_RPLIDAR_A2: {rplidar_data}")


            # Read from Cameras
            imx179_frame = read_imx179_camera()
            if imx179_frame is not None:
                # Process frame (e.g., cv2.imshow, object detection)
                logging.info("Frame captured from IMX179.")
                pass # remove pass for implementation

            flir_frame = read_flir_duo_pro_r_camera()
            if flir_frame is not None:
                # Process frame
                 logging.info("Frame captured from FLIR.")
                 pass # remove pass for implementation


            usb_camera_frame = read_usb_camera_5mpx_camera()
            if usb_camera_frame is not None:
                # Process frame
                 logging.info("Frame captured from USB Camera.")
                 pass # remove pass for implementation

            fish_eye_frame = read_fish_eye_lens_camera()
            if fish_eye_frame is not None:
                # Process frame
                 logging.info("Frame captured from Fish Eye Camera.")
                 pass # remove pass for implementation


            time.sleep(0.1)  # Example: Delay for 100ms. Adjust as needed.

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        cleanup_all()
