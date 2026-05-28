import requests
import os
import re
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import zipfile
import uvicorn

app = FastAPI()

class GenerateRequest(BaseModel):
    email: str
    project_name: str


def extract_code(text):
    matches = re.findall(r'```(?:[a-zA-Z0-9]*)\n(.*?)```', text, re.DOTALL)
    if matches:
        return "\n".join(matches)
    return text.strip()

def update_status(email, project_name, status_value):
    # Post to both development (192.168.50.161) and production (192.168.50.247) main servers
    for ip in ["192.168.50.161", "192.168.50.247"]:
        try:
            requests.post(f"http://{ip}:8080/process_endtrigger", json={
                "email": email,
                "project_name": project_name,
                "status_type": "synthesis",
                "status": status_value
            }, timeout=2.0)
        except Exception as e:
            print(f"Failed to post status to {ip}:", e)

@app.post("/download_nodecode")
def download_nodecode(request: GenerateRequest):
    email = request.email
    project_name = request.project_name
    project_dir = os.path.join("Client_code_generator", email, project_name)
    
    if not os.path.exists(project_dir):
        raise HTTPException(status_code=404, detail="Project code not found")
        
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project_dir)
                zipf.write(file_path, arcname)
    temp_zip.close()
    return FileResponse(temp_zip.name, media_type="application/zip", filename=f"{project_name}_code.zip")

@app.post("/post_nodecode")
def generate_code(request: GenerateRequest):


    email = request.email
    project_name = request.project_name

    # Always fetch reqdat at the start so it is defined for all usages
    reqdat = requests.post("http://192.168.50.247:8774/get_node_code",json={"email":email,"project_name":project_name}).json()['drawflow']['Home']['data']

    # Check if the connection list of the output is blank or not blank
    for node_id, node_data in reqdat.items():
        outputs = node_data.get('outputs', {})
        for output_name, output_info in outputs.items():
            connections = output_info.get('connections', [])
            if not connections:
                print(f"Node {node_id} output '{output_name}' has a blank connection list.")
            else:
                print(f"Node {node_id} output '{output_name}' has connections: {connections}")

    update_status(email, project_name, "Started generating node components...")

    # Clean up previously generated directories for this project
    project_base_dir = os.path.join("Client_code_generator", email, project_name)
    for dir_name in ["middleware", "firmware", "Installer"]:
        dir_path = os.path.join(project_base_dir, dir_name)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"Cleaned up old directory: {dir_path}")
            except Exception as e:
                print(f"Failed to clean up {dir_path}: {e}")

    optimize_select = requests.get("http://192.168.50.247:9060/get_optimize_select").json()[email][project_name] #Getting the optimize select for the components and category of the components inside the list 
    try:
        robot_desc_req = requests.get("http://192.168.50.247:9060/get_robot_description").json()
        robot_description = robot_desc_req.get(email, {}).get(project_name, "")
    except Exception as e:
        print(f"Error fetching robot description: {e}")
        robot_description = ""

    SERVICE_URLS = {
        'storage': 'http://192.168.50.247:9060',
        'gemini': 'http://192.168.50.247:9886',
        'semantic_match': 'http://192.168.50.4:8466',
        'component_extract': 'http://192.168.50.161:4972',
        'mcu_db': 'http://192.168.50.247:5978',
        'node_store': 'http://192.168.50.247:8774',
        'component_request': 'http://192.168.50.4:7795',
        'llm_helper': 'http://192.168.50.4:8332',
        'search_service': 'http://192.168.50.247:9767',
        'restart_service': 'http://192.168.50.247:5987',
        'classcomp': 'http://192.168.50.247:9060/get_classcomp'
    }
    ROBOREACTOR_COMPUTER_VISION_HARDWARE_MAP = {
  "vision_profiles": {
    "RPI_ZERO_2W": {
      "hardware": {
        "cpu": "Quad Cortex-A53",
        "ram_mb": 512,
        "gpu": "VideoCore IV",
        "ai_acceleration": False,
        "recommended_resolution": [
          "320x240",
          "416x416",
          "640x480"
        ],
        "camera_backend": [
          "Picamera2",
          "V4L2",
          "OpenCV"
        ]
      },
      "opencv_support": {
        "image_processing": {
          "status": "excellent",
          "fps": "20-30",
          "functions": [
            "cv2.Canny",
            "cv2.GaussianBlur",
            "cv2.threshold",
            "cv2.adaptiveThreshold",
            "cv2.erode",
            "cv2.dilate",
            "cv2.morphologyEx",
            "cv2.equalizeHist",
            "cv2.resize",
            "cv2.flip",
            "cv2.rotate",
            "cv2.filter2D",
            "cv2.Sobel",
            "cv2.Laplacian"
          ]
        },
        "aruco_and_marker": {
          "status": "excellent",
          "fps": "15-30",
          "functions": [
            "cv2.aruco.detectMarkers",
            "cv2.aruco.drawDetectedMarkers",
            "cv2.aruco.estimatePoseSingleMarkers",
            "cv2.solvePnP",
            "cv2.QRCodeDetector",
            "AprilTag"
          ]
        },
        "feature_detection": {
          "status": "good",
          "fps": "10-20",
          "functions": [
            "cv2.ORB_create",
            "cv2.BRISK_create",
            "cv2.FastFeatureDetector_create",
            "cv2.goodFeaturesToTrack",
            "cv2.cornerHarris"
          ]
        },
        "tracking": {
          "status": "good",
          "fps": "10-20",
          "functions": [
            "cv2.calcOpticalFlowPyrLK",
            "cv2.calcOpticalFlowFarneback",
            "cv2.meanShift",
            "cv2.CamShift"
          ]
        },
        "robot_navigation": {
          "status": "excellent",
          "applications": [
            "line_following",
            "lane_detection",
            "wall_following",
            "obstacle_detection",
            "visual_odometry",
            "basic_slam",
            "aruco_navigation",
            "qr_navigation"
          ]
        },
        "dnn_ai": {
          "status": "moderate",
          "fps": "1-5",
          "supported_models": [
            "YOLOv5n",
            "YOLOv8n",
            "NanoDet",
            "MobileNetSSD",
            "EfficientDetLite"
          ]
        }
      }
    },
    "RPI_4": {
      "hardware": {
        "cpu": "Quad Cortex-A72",
        "ram_options_gb": [2, 4, 8],
        "gpu": "VideoCore VI",
        "ai_acceleration": False,
        "recommended_resolution": [
          "640x480",
          "720p"
        ]
      },
      "opencv_support": {
        "image_processing": "excellent",
        "aruco": "excellent",
        "optical_flow": "excellent",
        "feature_matching": "excellent",
        "monocular_slam": "good",
        "stereo_vision": "moderate",
        "tiny_yolo": "good",
        "medium_yolo": "limited",
        "pose_estimation": "moderate",
        "face_detection": "good",
        "object_tracking": "good",
        "depth_estimation": "moderate"
      },
      "recommended_robotics_tasks": [
        "autonomous_navigation",
        "warehouse_robotics",
        "swarm_control",
        "digital_twin_streaming",
        "sensor_fusion",
        "vision_processing"
      ]
    },
    "RPI_5": {
      "hardware": {
        "cpu": "Quad Cortex-A76",
        "ram_options_gb": [4, 8],
        "gpu": "VideoCore VII",
        "ai_acceleration": False,
        "recommended_resolution": [
          "720p",
          "1080p"
        ]
      },
      "opencv_support": {
        "image_processing": "excellent",
        "aruco": "excellent",
        "dense_optical_flow": "good",
        "stereo_vision": "good",
        "monocular_slam": "excellent",
        "rtabmap": "moderate",
        "yolov5": "good",
        "yolov8n": "good",
        "pose_estimation": "good",
        "segmentation": "moderate",
        "multi_camera": "moderate"
      },
      "recommended_robotics_tasks": [
        "advanced_navigation",
        "robot_digital_twin",
        "vision_ai_processing",
        "multi_sensor_fusion",
        "mapping",
        "slam"
      ]
    },
    "ORANGE_PI": {
      "hardware": {
        "cpu": "RK3588 / H618 dependent",
        "ram_options_gb": [2, 4, 8, 16],
        "gpu": "Mali GPU",
        "npu": "up to 6 TOPS on RK3588"
      },
      "opencv_support": {
        "image_processing": "excellent",
        "aruco": "excellent",
        "slam": "good",
        "tiny_yolo": "excellent",
        "yolov8": "good",
        "segmentation": "moderate",
        "pose_estimation": "good",
        "stereo_depth": "good"
      },
      "recommended_robotics_tasks": [
        "edge_ai",
        "robotics_ai",
        "local_inference",
        "vision_navigation"
      ]
    },
    "BANANA_PI": {
      "hardware": {
        "cpu": "ARM Cortex series",
        "ram_options_gb": [2, 4, 8],
        "gpu": "Mali GPU"
      },
      "opencv_support": {
        "image_processing": "excellent",
        "aruco": "excellent",
        "tiny_yolo": "moderate",
        "slam": "moderate",
        "tracking": "good"
      }
    },
    "JETSON_NANO": {
      "hardware": {
        "cpu": "Quad Cortex-A57",
        "ram_gb": 4,
        "gpu": "128-core Maxwell CUDA",
        "cuda": True,
        "tensor_rt": True
      },
      "opencv_support": {
        "image_processing": "excellent",
        "aruco": "excellent",
        "slam": "good",
        "yolov5": "good",
        "yolov8": "good",
        "segmentation": "moderate",
        "pose_estimation": "good",
        "depth_ai": "good",
        "stereo_depth": "good"
      },
      "recommended_robotics_tasks": [
        "autonomous_robotics",
        "ai_navigation",
        "vision_ai",
        "slam",
        "edge_inference"
      ]
    },
    "JETSON_ORIN_NANO": {
      "hardware": {
        "cpu": "6-core ARM A78AE",
        "gpu": "1024-core Ampere",
        "tensor_cores": 32,
        "ram_gb": [4, 8],
        "ai_performance_tops": 40
      },
      "opencv_support": {
        "image_processing": "excellent",
        "aruco": "excellent",
        "slam": "excellent",
        "rtabmap": "excellent",
        "yolov8": "excellent",
        "segmentation": "excellent",
        "pose_estimation": "excellent",
        "depth_estimation": "excellent",
        "multi_camera": "excellent"
      },
      "recommended_robotics_tasks": [
        "industrial_robotics",
        "advanced_ai",
        "3d_mapping",
        "multi_robot_coordination",
        "digital_twin"
      ]
    },
    "NUC_PC": {
      "hardware": {
        "cpu": "Intel i5/i7/i9",
        "ram_options_gb": [8, 16, 32, 64],
        "gpu": [
          "Intel Xe",
          "NVIDIA GPU optional"
        ]
      },
      "opencv_support": {
        "all_opencv_functions": "excellent",
        "slam": "excellent",
        "dense_mapping": "excellent",
        "yolov8_large": "excellent",
        "segmentation": "excellent",
        "transformer_ai": "good",
        "3d_reconstruction": "excellent",
        "gaussian_splatting": "moderate"
      },
      "recommended_robotics_tasks": [
        "robotics_server",
        "fleet_management",
        "simulation",
        "training_ai_models",
        "digital_twin_server",
        "centralized_ai"
      ]
    },
    "GENERIC_COMPUTER": {
      "hardware": {
        "cpu": "x86_64 or ARM",
        "ram_gb": "variable",
        "gpu": "optional"
      },
      "opencv_support": {
        "basic_vision": "excellent",
        "aruco": "excellent",
        "tracking": "excellent",
        "slam": "depends_on_hardware",
        "ai_inference": "depends_on_gpu"
      },
      "robotics_role": [
        "development_machine",
        "simulation_machine",
        "vision_processing",
        "robotics_control_server"
      ]
    }
  },
  "global_supported_computer_vision_applications": [
    "aruco_navigation",
    "apriltag_localization",
    "qr_navigation",
    "line_following",
    "lane_detection",
    "optical_flow",
    "visual_odometry",
    "monocular_slam",
    "stereo_vision",
    "feature_matching",
    "object_tracking",
    "motion_detection",
    "face_detection",
    "gesture_detection",
    "pose_estimation",
    "object_detection",
    "semantic_segmentation",
    "depth_estimation",
    "3d_mapping",
    "point_cloud_processing",
    "digital_twin_visualization",
    "robot_navigation",
    "warehouse_robotics",
    "swarm_robotics",
    "industrial_robotics",
    "drone_navigation"
  ]
}
    commu_mapnode = {
          "SBC_node": 
          { 
            "input":{ 
            "Serial":"input_1", 
            "Camera": "input_2", 
            "UART": "input_3", 
            "GPIO": "input_4",
             "I2C": "input_5", 
             "SPI": "input_6",
             "CSI":"input_7",
             "I2S":"input_8",
            
             }, 
             "output":{ 
              "Logic_control":"output_1" 
              } 
              }, 
            "mcus_node": 
            { 
             "input":{ 
               #"Serial":"input_1",
               "UART": "input_1", 
               "Servo": "input_2", 
               "PWM": "input_3", 
               "Digital": "input_4", 
               "DAC": "input_5", 
               "Analog": "input_6", 
                "I2C": "input_7", 
                "CAN": "input_8", 
                "SPI": "input_9"
              
               },
              "output":{ 
                "Serial":"output_1",
                "PWM":"output_2"
                } 
                }, 
            "Servo_multiplexer": { 
              "output": { 
                "I2C": "output_1",
                "VCC": "output_3", 
                "GND": "output_3", 
                "PWM": "output_4" 
                }, 
                "input": { 
                  "OE": "input_1",
                  "PWM": "input_2" 
                  } }, 
            "I2C_multiplexer": {
              "input": {
                "I2C": "input_1"
              },
              "output": {
                "I2C": "output_1"
              }
            },
            "DC_motor_driver":{ 
              "input": { 
                "VCC": "input_1",
                "GND": "input_2" 
              }, 
              "output": { 
                "PWM": "output_1", 
                "Digital": "output_2",
                "Motor_A": "output_3", 
                "Motor_B": "output_4" 
                } 
              }, 
            "Stepper_motor_driver": { 
              "input": { 
                "VCC": "input_1", 
                "GND": "input_2"
              }, 
              "output": { 
                "Digital": "output_1", 
                "Digital_2": "output_2",
                "Digital_3": "output_3",
                "Coil_A": "output_4", 
                "Coil_B": "output_5" 
                } }, 
            "BLDC_motor_driver": { 
              "input": { 
                "VCC": "input_1", 
                "GND": "input_2"
               }, 
               "output": { 
                "PWM": "output_1",
                "Phase_U": "output_2", 
                "Phase_V": "output_3",
                "Phase_W": "output_4", 
                "Telemetry": "output_5"
                 } }, 
             "Flight_controller": { 
              "input": { 
                "IMU": "input_1", 
                "GPS": "input_2", 
                "PWM": "input_3", 
                "RC_Input": "input_4" 
                }, 
             "output": { 
              "UART": "output_1", 
              "Telemetry": "output_2",
              "PWM": "output_3"
              } 
              }, 
           "ESC_electronics_speed_controller": { 
            "output": { 
              "PWM": "output_1",
              "Phase_V": "output_2",
              "Phase_W": "output_3",
              "RPM_Feedback": "output_4" 
             }, 
             "input": { 
              "PWM": "input_1", 
              "VBAT": "input_2", 
              "GND": "input_3" }
            }, 
          "servo_motor": { 
           "input": { 
            "PWM": "input_1", 
            "VCC": "input_2", 
            "GND": "input_3" 
            }, 
            "output": { 
              "Angle": "output_1"
               }
            },
           "USB_camera": {
            "input": {
              "camera_detection": "input_1",
              "VCC": "input_2",
              "GND": "input_3"
            },
            "output": {
              "Serial": "output_1"
            }
           },
           "CSI_camera": {
            "input": {
              "camera_detection": "input_1",
              "VCC": "input_2",
              "GND": "input_3"
            },
            "output": {
              "CSI": "output_1"
            }
           },
           "LIDAR": {
            "input": {
              "scan_cmd": "input_1",
              "VCC": "input_2",
              "GND": "input_3"
            },
            "output": {
              "cloud_point": "output_1",
              "Serial": "output_2"
            }
           },
           "GPS": {
            "input": {
              "VCC": "input_1",
              "GND": "input_2"
            },
            "output": {
              "nmea_data": "output_1",
              "UART": "output_2"
            }
           },
           "Ultrasonic_sensor": {
            "input": {
              "trigger": "input_1",
              "VCC": "input_2",
              "GND": "input_3"
            },
            "output": {
              "Digital": "output_1"
            }
           },
           "navigation_input": {
            "input": {
              "waypoints": "input_1",
              "map_data": "input_2"
            },
            "output": {
              "navigation_status": "output_1",
              "target_pose": "output_2"
            }
           },
           "stepper_motor": {
            "input": { 
              "Coil_A": "input_1", 
              "Coil_B": "input_2" 
            }, 
            "output": { 
              "Position": "output_1" 
              }
           },
           "IMU": {
            "input": {
              "VCC": "input_1",
              "GND": "input_2"
            },
            "output": {
              "I2C": "output_1",
              "gyro": "output_2",
              "mag": "output_3"
            }
           },
           "Distance_sensor": {
            "input": {
              "VCC": "input_1",
              "GND": "input_2"
            },
            "output": {
              "Analog": "output_1"
            }
           },
           "Force_sensor": {
            "input": {
              "VCC": "input_1",
              "GND": "input_2"
            },
            "output": {
              "Analog": "output_1"
            }
           },
           "Proximity_sensor": {
            "input": {
              "VCC": "input_1",
              "GND": "input_2"
            },
            "output": {
              "Digital": "output_1"
            }
           },
           "Encoder": {
            "input": {
              "VCC": "input_1",
              "GND": "input_2"
            },
            "output": {
              "Digital": "output_1",
              "Digital_2": "output_2"
            }
           },
          "dc_motor": { 
            "output": { 
              "PWM": "input_1", 
              "PWM": "input_2" 
              }, 
            "input": { 
              "Rotation": "output_1" 
              }
         }, 
            "bldc_motor": { 
              "output": { 
                "PWM": "input_1", 
                "PWM": "input_2", 
                "PWM": "input_3" 
              }, 
             "input": { 
              "RPM": "output_1" 
              } 
            }, 
            "Duct_fan_thruster": 
            { "output": { 
              "PWM": "output_1", 
              "VCC": "output_2", 
              "GND": "output_3" 
              }, 
            "input": { 
              "PWM": "input_1" 
              } 
            }, 
          "Cellular_LTE":{
               "input":{
                    "VCC":"input_1",
                    "GND":"input_2",
                    "Antenna":"input_3"
               },
               "output":{
                    "Serial":"output_1"
               }   
          },
          "Micro_jet_engine": { 
            "input": { 
              "Fuel": "input_1", 
              "Ignition": "input_2", 
              "PWM": "input_3" }, 
            "output": { 
              "Thrust": "output_1" 
              } 
            },
            "Audio_amplifier": {
              "input": { "VCC": "input_1", "GND": "input_2", "Analog": "input_3" },
              "output": { "Speaker+": "output_1", "Speaker-": "output_2" }
            },
            "USB_sound_card": {
              "input": { "Analog": "input_1" },
              "output": { "Serial": "output_1", "I2S": "output_3", "Analog": "output_2" }
            },
            "Microphone": {
              "input": { "VCC": "input_1", "GND": "input_2" },
              "output": { "Analog": "output_1" }
            },
            "Speaker": {
              "input": { "In+": "input_1", "In-": "input_2" },
              "output": { "Audio_Status": "output_1" }
            }
          }
    id_device_mapping = {} #Getting the id device mapping for th node id data processing 
    totalcomp_class = requests.get("http://192.168.50.247:9060/get_classcomp").json() #Getting the total components class selection 
    def semantic_processing(aiselectclass,comp):
         sem_resp = requests.post(
            f"{SERVICE_URLS['semantic_match']}/processing_part_match",
            json={email: {"project_name": project_name, 'command': aiselectclass, 'ref_data': comp}}
         )
         sem_json = sem_resp.json()
         compclassdat = sem_json.get('max_command')
         return compclassdat #Getting the return semantic selection data 
    #Mapping the list of the navigation 
    if email not in id_device_mapping:
        id_device_mapping[email] = {}
    if project_name not in id_device_mapping[email]:
        id_device_mapping[email][project_name] = {}

    for node_id in reqdat:
        # Ensure node_id is treated as a string for mapping consistency
        id_device_mapping[email][project_name][str(node_id)] = reqdat[node_id]['name']
        print(f"Mapped node {node_id} to {reqdat[node_id]['name']}")

    req_processor = requests.get("http://192.168.50.247:9060/total_selected").json()[email][project_name]
    #Checking if the system found the single board computer inside the list of the total_selected or not 
    if "Single_Board_computer" in list(req_processor) and "Microcontroller" in list(req_processor):
        #Generate the code in the case where the system detected single board computer
        sbcname = req_processor["Single_Board_computer"]  #Getting the single board computer from the selected list of the components by the email input of the project 
        print("Get current SBC name: ",sbcname) 
        # Find the SBC node ID dynamically instead of hardcoding '1'
        sbc_node_id_found = None
        for n_id, n_data in reqdat.items():
            if n_data['name'].startswith(sbcname):
                sbc_node_id_found = n_id
                break
        
        if sbc_node_id_found:
            print(f"Found SBC node ID: {sbc_node_id_found}")
            sbc_nodeid = reqdat[sbc_node_id_found]["inputs"]
        else:
            print(f"Warning: Could not find node ID for SBC {sbcname}, falling back to node '1'")
            sbc_nodeid = reqdat.get('1', {}).get('inputs', {})
        #print("Serial device and processing: ",sbc_nodeid)
        #Checking the device serial first 
        #for dev in sbc_nodeid:
        port_io  = commu_mapnode['SBC_node']['input']["Serial"] #Getting the list of the serial protocol device 
        print("List connection for serial: ",sbc_nodeid[port_io]) #Getting the list of the serial connection       
        #Getting the list of the port id connection 
        list_serialcom = sbc_nodeid[port_io]['connections'] #getting the list port io data 
        print("Getting the list port",list_serialcom)   
        store_mcusserial = {} #Store the mcus node inside the    
        store_sensorserial = {} #Store other serial sensors
        store_mainbridge_proc= {} #Store other sub components for sub processing chip part in the connection like I2C_mux ADC_mux Servo mux CAN-bus mux 
        for c_id in list_serialcom: 
             #print("Get node id connection: ",c_id) #Getting the serial connection   
             node_serial =c_id['node']  #Getting the node name  
             #print("Serial node name: ",node_serial) #Getting theserial data of the node
             #Getting the device name from the mapping data 
             node_id_str = str(node_serial)
             if node_id_str in id_device_mapping[email][project_name]:
                 dev_name = id_device_mapping[email][project_name][node_id_str]
                 print("Getting device name: ", dev_name)
                 # Clean dev_name by removing the last node ID number (suffix like _92)
                 dev_name_parts = str(dev_name).split("_")
                 if len(dev_name_parts) > 1:
                     dev_name = "_".join(dev_name_parts[:-1])
                 print("Cleaned device name for AI: ", dev_name)

             else:
                 print(f"Warning: Serial node ID {node_id_str} not found in id_device_mapping")
                 continue # Skip this connection if node is unknown
             #Checking the device name and category existing map data 
             device_catcheck = {}
             try:
                 cat_data = requests.get("http://192.168.50.247:9074/getdevice_cat").json()
                 if email in cat_data and project_name in cat_data[email]:
                     device_catcheck = cat_data[email][project_name]
             except Exception as e:
                  print(f"Error requesting the device category: {e}")  
             if dev_name not in device_catcheck:
                 #Use the semantic processing to get the components name and the device class components 
                 categ_list = list(req_processor) #Getting the list category of the components from the list of the components serial device connection 
                 update_status(email, project_name, f"Selecting semantic category for {dev_name}...")
                 #Use AI select from the list first to get the cateogory from the components selection 
                 aiagent_search = requests.post(SERVICE_URLS['gemini']+"/ask_gemini",json={"email":email,"project_name":project_name,"command":f"Select the category of the component {dev_name} from the list {categ_list} answer in single word selected from the list "}).json()[email]
                 print("AI selected category: ",aiagent_search)
                 semanticselect = semantic_processing(aiagent_search,categ_list) #Getting the semantic serial device connection from the list by semantically selection 
                 print("Semantic select: ",semanticselect) 
                 try:
                     reqcatstore = requests.post("http://192.168.50.247:9074/device_mappost",json={"email":email,"project_name":project_name,"category_payload":{dev_name:semanticselect}}) #Getting the category mapping with the device name data 
                 except:
                     print("Category server post requets error") #Getting the category mapping error 
             else:
                 semanticselect = device_catcheck[dev_name]
                 print("Using cached category for: ", dev_name, " -> ", semanticselect)
             
             #Mapping the data to the server to store the category of the components existing categorization to reduce AI usage 
             #Mcus from total select detection for the connection list extraction 
             #Checking only the microcntroller node detection 
             if semanticselect == "Microcontroller":
                     #Getting the id from the microcontroller detected 
                     mcus_nodeconnect_in = reqdat[node_id_str].get('inputs', {})
                     mcus_nodeconnect_out = reqdat[node_id_str].get('outputs', {})
                     mcus_nodeconnect = {**mcus_nodeconnect_in, **mcus_nodeconnect_out}
                     print("mcus_nodeconnectlist: ",mcus_nodeconnect)
                     store_mcusserial[dev_name]  =  mcus_nodeconnect
             else:
                     print(f"Non-MCU Serial device detected: {dev_name} ({semanticselect})")
                     store_sensorserial[dev_name] = semanticselect
        
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("Store Serial device (MCUs): ",store_mcusserial) #Getting the store mcus device connection list 
        print("Store Serial device (Sensors): ",store_sensorserial)
        #For loop each mcus to scanning for the list of the device connection from the node id 
        store_direct_terminal_proc = {} # To store terminal components directly connected to MCU
        for mcsr in list(store_mcusserial):  
                print(mcsr,store_mcusserial[mcsr])
                for mcyr in store_mcusserial[mcsr]:
                   if store_mcusserial[mcsr][mcyr]['connections'] != []:
                     print(mcsr,mcyr,store_mcusserial[mcsr][mcyr]['connections']) #Getting the list of the components connection inside data 
                     for list_connect in store_mcusserial[mcsr][mcyr]['connections']:
                                 target_node_id = str(list_connect['node'])
                                 if target_node_id in id_device_mapping[email][project_name]:
                                     print("Get the device name from node number", target_node_id, id_device_mapping[email][project_name][target_node_id])
                                     target_dev_name_raw = id_device_mapping[email][project_name][target_node_id]
                                     target_dev_name_parts = str(target_dev_name_raw).split("_")
                                     if len(target_dev_name_parts) > 1:
                                         target_dev_name = "_".join(target_dev_name_parts[:-1])
                                     else:
                                         target_dev_name = target_dev_name_raw
                                     
                                     device_catcheck = {}
                                     try:
                                         cat_data = requests.get("http://192.168.50.247:9074/getdevice_cat").json()
                                         if email in cat_data and project_name in cat_data[email]:
                                             device_catcheck = cat_data[email][project_name]
                                     except Exception as e:
                                         print(f"Error requesting the device category: {e}")
                                     
                                     if target_dev_name not in device_catcheck or device_catcheck[target_dev_name] not in commu_mapnode.keys():
                                         categ_list = list(commu_mapnode.keys())
                                         aiagent_search = requests.post(SERVICE_URLS['gemini']+"/ask_gemini",json={"email":email,"project_name":project_name,"command":f"Select the category of the component {target_dev_name} from the list {categ_list} answer in single word selected from the list "}).json()[email]
                                         semanticselect_target = semantic_processing(aiagent_search,categ_list)
                                         # Cache the result regardless of what it is, so we never process it in AI search again
                                         try:
                                             reqcatstore = requests.post("http://192.168.50.247:9074/device_mappost",json={"email":email,"project_name":project_name,"category_payload":{target_dev_name:semanticselect_target}})
                                         except:
                                             print("Category server post requets error")
                                             
                                         if semanticselect_target in ["ADC mux","Servo_multiplexer", "I2C_mux", "I2C_multiplexer", "Flight_controller"]:
                                             print(f"Detected Component: {target_dev_name} -> {semanticselect_target}")
                                     else:
                                         semanticselect_target = device_catcheck[target_dev_name]
                                         print(f"Using cached Component: {target_dev_name} -> {semanticselect_target}")
                                     
                                     # Store component regardless of whether it was cached or freshly fetched
                                     if semanticselect_target in ["ADC mux","Servo_multiplexer", "I2C_mux", "I2C_multiplexer", "Flight_controller"]:
                                         if semanticselect_target not in store_mainbridge_proc:
                                             print("Store the device mapping by the category of the sub node component detected")
                                             store_mainbridge_proc[semanticselect_target] = [] 
                                         if target_dev_name_raw not in store_mainbridge_proc[semanticselect_target]:
                                             store_mainbridge_proc[semanticselect_target].append(target_dev_name_raw)
                                     else:
                                         if semanticselect_target not in store_direct_terminal_proc:
                                             print("Store the direct terminal component to the MCU")
                                             store_direct_terminal_proc[semanticselect_target] = []
                                         if target_dev_name_raw not in store_direct_terminal_proc[semanticselect_target]:
                                             store_direct_terminal_proc[semanticselect_target].append(target_dev_name_raw)
                                 else:
                                     print(f"Warning: Node ID {target_node_id} not found in id_device_mapping")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.")
        print("Get mainbridge component protocol: ",store_mainbridge_proc)
        print("Get direct terminal components: ",store_direct_terminal_proc)
        store_terminal_connections = {}
        for mainbrige_ri in list(store_mainbridge_proc):
                      print(mainbrige_ri,store_mainbridge_proc[mainbrige_ri])
                      for m_cse in store_mainbridge_proc[mainbrige_ri]:
                              if m_cse not in store_terminal_connections:
                                  store_terminal_connections[m_cse] = []
                              print("Checking conneciton bridge inside ",m_cse) #getting the each main bridge connection list 
                              mc_len = len(str(m_cse).split("_")) #Getting the m_cse len for the components name 
                              idcomp = str(m_cse).split("_")[mc_len-1] 
                              print(m_cse," ID components :",idcomp)
                              print("Main bridge component: ",m_cse,reqdat[idcomp]) #Getting the main bridge components from the id input data 
                              
                              if 'inputs' in reqdat[idcomp]:
                                  for input_port in reqdat[idcomp]['inputs']:
                                      for conn in reqdat[idcomp]['inputs'][input_port]['connections']:
                                          conn_node_id = str(conn['node'])
                                          if conn_node_id in id_device_mapping[email][project_name]:
                                              conn_dev_name = id_device_mapping[email][project_name][conn_node_id]
                                              print(f"Main bridge {m_cse} Input connected to: Node {conn_node_id} -> {conn_dev_name}")
                                              raw_node_name = reqdat[conn_node_id]['name']
                                              print("Node components connected: ",raw_node_name)
                                              store_terminal_connections[m_cse].append(raw_node_name)
                                              
                              if 'outputs' in reqdat[idcomp]:
                                  for output_port in reqdat[idcomp]['outputs']:
                                      for conn in reqdat[idcomp]['outputs'][output_port]['connections']:
                                          conn_node_id = str(conn['node'])
                                          if conn_node_id in id_device_mapping[email][project_name]:
                                              conn_dev_name = id_device_mapping[email][project_name][conn_node_id]
                                              print(f"Main bridge {m_cse} Output connected to: Node {conn_node_id} -> {conn_dev_name}")
                                              raw_node_name = reqdat[conn_node_id]['name']
                                              print("Node components connected: ",raw_node_name)
                                              store_terminal_connections[m_cse].append(raw_node_name)
                        
                      print("---------------------------------------------------------------------------")
                      
        print("Terminal Connections Map (via Bridge): ", store_terminal_connections)
        
        print("\n--- Generating SBC Middleware ---")
        update_status(email, project_name, f"Generating SBC Middleware for {sbcname}...")
        sbc_prompt = f"Generate Python middleware code for a single board computer ({sbcname})."
        if store_mcusserial:
            sbc_prompt += f" It needs to establish Serial communication with the following microcontrollers: {list(store_mcusserial.keys())}."
        if store_sensorserial:
            sbc_prompt += f" It needs to establish Serial communication and processing for the following serial sensors/devices (Device Name -> Category map): {store_sensorserial}. Include appropriate libraries based on the device category (e.g., import cv2 for vision/camera systems, parsers for LIDAR/GPS, etc.). For any camera/vision devices, ensure the code includes a function to dynamically scan and detect available camera port indices (e.g., 0, 1, 2... up to n) rather than using string names for camera initialization."
        if robot_description:
            sbc_prompt += f" The overall robot description is: '{robot_description}'. Please use this description to select the specific and appropriate computer vision functions and processing logic for the vision system detected."
            sbc_prompt += " If the robot description requires object detection, you MUST use YOLOv8 with the `ultralytics` library instead of cv2 object detection alone."
            try:
                # Inject YOLOv8 example into the prompt
                yolo_example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolov8_realtime.py")
                with open(yolo_example_path, "r") as yolo_file:
                    yolo_example = yolo_file.read()
                sbc_prompt += f" Use this example code as a reference for YOLOv8 object detection implementation:\n```python\n{yolo_example}\n```\n"
            except Exception as e:
                print(f"Error reading YOLOv8 example: {e}")
        sbc_prompt += " Include the required imports (like pyserial) and create empty functions for reading from and writing to these devices so the control logic can be added later. Do not include implementation, only the skeleton structure. Output ONLY the code, with no explanation."
        try:
            sbc_code_response = requests.post(SERVICE_URLS['gemini']+"/ask_gemini", json={"email":email, "project_name":project_name, "command": sbc_prompt}).json()[email]
            print("SBC Middleware Generated:\n", sbc_code_response)
            sbc_code_extracted = extract_code(sbc_code_response)
            middleware_dir = os.path.join("Client_code_generator", email, project_name, "middleware")
            os.makedirs(middleware_dir, exist_ok=True)
            with open(os.path.join(middleware_dir, "middleware.py"), "w") as f:
                f.write(sbc_code_extracted)
            print(f"SBC Middleware saved to {middleware_dir}/middleware.py")
            
            # Generate installer script with hardware detection for fresh OS
            installer_dir = os.path.join("Client_code_generator", email, project_name, "Installer")
            os.makedirs(installer_dir, exist_ok=True)
            installer_script_path = os.path.join(installer_dir, "install_dependencies.sh")
            
            bash_script = """#!/bin/bash
    echo "Starting Installation..."
    echo "Updating system and installing base dependencies..."
    sudo apt-get update
    sudo apt-get install -y curl git build-essential python3 python3-pip python3-venv python3-opencv

    echo "Detecting System Specifications..."
    # Detect Memory
    TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
    echo "Total Memory: ${TOTAL_MEM} MB"

    # Detect Python Version and verify compatibility (Ultralytics requires Python >= 3.8)
    echo "Checking Python Version Compatibility..."
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is not installed on this system."
        exit 1
    fi
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    echo "Detected Python: ${PYTHON_MAJOR}.${PYTHON_MINOR}"
    if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -lt 8 ]; then
        echo "Error: Python 3.8 or higher is required to run the generated middleware libraries (ultralytics/YOLOv8)."
        echo "Please upgrade your Python installation and try again."
        exit 1
    fi

    # Detect SBC or Laptop
    IS_SBC=0
    if [ -f /sys/firmware/devicetree/base/model ]; then
        MODEL=$(tr -d '\\0' < /sys/firmware/devicetree/base/model)
        echo "Detected SBC Model: $MODEL"
        IS_SBC=1
    else
        echo "Generic PC/Laptop detected."
    fi

    # CPU Architecture
    ARCH=$(uname -m)
    echo "Architecture: $ARCH"

    # Installing/Updating Rust Language Compiler
    echo "Checking Rust Compiler..."
    if command -v rustc &> /dev/null; then
        echo "Rust is already installed. Checking for updates..."
        if command -v rustup &> /dev/null; then
            rustup update stable
        else
            echo "rustup not found. Attempting to update rustc and cargo via apt..."
            sudo apt-get install -y --only-upgrade rustc cargo
        fi
    else
        echo "Rust is not installed. Installing Rust via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        if [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        fi
    fi

    # Verify Rust compiler setup and fallback if needed
    if command -v rustc &> /dev/null; then
        echo "Rust compiler verified successfully:"
        rustc --version
        cargo --version
    else
        echo "rustup environment not loaded. Attempting fallback installation via apt..."
        sudo apt-get install -y rustc cargo
        if command -v rustc &> /dev/null; then
            echo "Rust compiler installed via apt:"
            rustc --version
        else
            echo "Warning: Rust compiler could not be set up. Some libraries requiring Rust compilation might fail to install."
        fi
    fi

    # Detect memory requirements specifically before Ollama installation
    echo "Checking memory requirements for Ollama..."
    if [ -n "$TOTAL_MEM" ] && [ "$TOTAL_MEM" -eq "$TOTAL_MEM" ] 2>/dev/null; then
        if [ "$TOTAL_MEM" -lt 4000 ]; then
            echo "Warning: System memory is ${TOTAL_MEM} MB (less than 4GB)."
            echo "Ollama and its LLM models run best with at least 4GB of RAM."
            echo "Proceeding with Ollama installation, but performance may be slow or unstable."
        else
            echo "Memory check passed: ${TOTAL_MEM} MB is sufficient for Ollama."
        fi
    else
        echo "Warning: Could not determine total memory accurately. Proceeding anyway."
    fi

    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sudo sh

    echo "Creating Python Virtual Environment (venv)..."
    # Create venv at the project root directory (one level up from Installer folder)
    python3 -m venv "$(dirname "$0")/../venv"

    # Create a custom temporary directory for pip to avoid running out of space in /tmp (common on SBCs)
    PIP_TMP_DIR="$(dirname "$0")/../pip_tmp"
    mkdir -p "$PIP_TMP_DIR"
    export TMPDIR="$PIP_TMP_DIR"

    echo "Upgrading pip inside virtual environment..."
    "$(dirname "$0")/../venv/bin/pip" install --upgrade pip

    echo "Installing YOLOv8 (ultralytics), OpenCV, FastAPI, and Uvicorn inside virtual environment..."
    "$(dirname "$0")/../venv/bin/pip" install ultralytics opencv-python fastapi uvicorn

    # Clean up custom pip temp dir
    rm -rf "$PIP_TMP_DIR"
    unset TMPDIR

    echo "Creating startup runner script (run.sh)..."
    RUN_SCRIPT_PATH="$(dirname "$0")/../run.sh"
    cat << 'EOF' > "$RUN_SCRIPT_PATH"
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ ! -d "${SCRIPT_DIR}/venv" ]; then
    echo "Error: Virtual environment (venv) directory not found at ${SCRIPT_DIR}/venv."
    echo "Please run the Installer/install_dependencies.sh script first."
    exit 1
fi
echo "Activating virtual environment and starting middleware..."
source "${SCRIPT_DIR}/venv/bin/activate"
python3 "${SCRIPT_DIR}/middleware/middleware.py"
EOF
    chmod +x "$RUN_SCRIPT_PATH"
    echo "Runner script created at: $RUN_SCRIPT_PATH"

    echo "Installation complete!"
    echo "To run your middleware within the virtual environment, execute:"
    echo "  python3 \"$(dirname "$0")/../middleware/middleware.py\" using the virtual env python:"
    echo "  \"$(dirname "$0")/../venv/bin/python3\" \"$(dirname "$0")/../middleware/middleware.py\""
    echo "Or run the startup script directly:"
    echo "  \"$(dirname "$0")/../run.sh\""
    """
            with open(installer_script_path, "w") as f:
                f.write(bash_script)
            
            # Make the script executable
            os.chmod(installer_script_path, 0o755)
            print(f"SBC Dependencies Installer saved to {installer_script_path}")
        except Exception as e:
            print("Error generating SBC Middleware:", e)

        print("\n--- Generating MCU Firmware ---")
        for mcu_dev in store_mcusserial.keys():
            update_status(email, project_name, f"Generating MCU Firmware for {mcu_dev}...")
            mcu_prompt = f"Generate Arduino (.ino) firmware skeleton for microcontroller {mcu_dev}. "
            mcu_prompt += f"It has direct components: {store_direct_terminal_proc}. "
            mcu_prompt += f"It is connected to bridges {store_mainbridge_proc}, which control these terminal components: {store_terminal_connections}. "
            mcu_prompt += "Include necessary Arduino libraries (e.g., Wire.h for I2C, Servo.h). Leave the setup() and loop() structures, and create empty functions for reading sensors and writing actuator commands. Output ONLY the code, with no explanation."
            try:
                mcu_code_response = requests.post(SERVICE_URLS['gemini']+"/ask_gemini", json={"email":email, "project_name":project_name, "command": mcu_prompt}).json()[email]
                print(f"MCU Firmware Generated for {mcu_dev}:\n", mcu_code_response)
                mcu_code_extracted = extract_code(mcu_code_response)
                firmware_dir = os.path.join("Client_code_generator", email, project_name, "firmware")
                os.makedirs(firmware_dir, exist_ok=True)
                with open(os.path.join(firmware_dir, f"{mcu_dev}_firmware.ino"), "w") as f:
                    f.write(mcu_code_extracted)
                print(f"MCU Firmware saved to {firmware_dir}/{mcu_dev}_firmware.ino")
            except Exception as e:
                print(f"Error generating MCU Firmware for {mcu_dev}:", e)

    elif "Single_Board_computer" in list(req_processor) and "Microcontroller" not in list(req_processor):
        print("Generate the code in the case only detected Single Board Computer in the system")
        sbcname = req_processor["Single_Board_computer"]
        print("Get current SBC name: ", sbcname)
        
        sbc_node_id_found = None
        for n_id, n_data in reqdat.items():
            if n_data['name'].startswith(sbcname):
                sbc_node_id_found = n_id
                break
        
        sbc_connected_devices = {}
        if sbc_node_id_found:
            sbc_node_in = reqdat[sbc_node_id_found].get('inputs', {})
            sbc_node_out = reqdat[sbc_node_id_found].get('outputs', {})
            sbc_node_io = {**sbc_node_in, **sbc_node_out}
            for port, port_data in sbc_node_io.items():
                if port_data.get('connections'):
                    for conn in port_data['connections']:
                        conn_node_id = str(conn['node'])
                        if conn_node_id in id_device_mapping[email][project_name]:
                            conn_dev_name = id_device_mapping[email][project_name][conn_node_id]
                            if port not in sbc_connected_devices:
                                sbc_connected_devices[port] = []
                            sbc_connected_devices[port].append(conn_dev_name)
        
        print(f"SBC {sbcname} (Node {sbc_node_id_found}) connections: {sbc_connected_devices}")
        
        sbc_prompt = f"Generate Python middleware code for a single board computer ({sbcname}). "
        sbc_prompt += "Since there is no Microcontroller detected in the system, this SBC connects to sensors and actuators directly via its own hardware pins. "
        sbc_prompt += f"The SBC is connected to the following components via specific ports: {sbc_connected_devices}. "
        sbc_prompt += "Ensure the generated Python code is based on the accurate hardware pin mapping of this specific SBC model (e.g., Raspberry Pi 3/4/5, Jetson Nano, Orange Pi, Banana Pi, etc.). "
        sbc_prompt += "Use appropriate Python libraries for direct SBC GPIO control (e.g., RPi.GPIO, Jetson.GPIO, smbus, spidev). "
        
        if robot_description:
            sbc_prompt += f" The overall robot description is: '{robot_description}'. Please use this description to select the specific computer vision and processing logic. "
            sbc_prompt += " If the robot description requires object detection, you MUST use YOLOv8 with the `ultralytics` library instead of cv2 object detection alone. "
        
        sbc_prompt += "Create empty functions for reading from and writing to these devices so control logic can be added later. Output ONLY the code, with no explanation."
        
        try:
            sbc_code_response = requests.post(SERVICE_URLS['gemini']+"/ask_gemini", json={"email":email, "project_name":project_name, "command": sbc_prompt}).json()[email]
            print("SBC Middleware Generated for direct GPIO mode:\n", sbc_code_response)
            sbc_code_extracted = extract_code(sbc_code_response)
            middleware_dir = os.path.join("Client_code_generator", email, project_name, "middleware")
            os.makedirs(middleware_dir, exist_ok=True)
            with open(os.path.join(middleware_dir, "middleware.py"), "w") as f:
                f.write(sbc_code_extracted)
            print(f"SBC Middleware (GPIO Mode) saved to {middleware_dir}/middleware.py")
        except Exception as e:
            print("Error generating SBC Middleware:", e)
                    
    if "Single_Board_computer" not in list(req_processor) and "Microcontroller" in list(req_processor):
        print("Generate the code in the case only detected Microcontroller in the system")
        mcu_name = req_processor["Microcontroller"]
        print("Get current MCU name: ", mcu_name)
        
        # Find MCU node IDs
        mcu_node_ids = []
        for n_id, n_data in reqdat.items():
            if n_data['name'].startswith(mcu_name):
                mcu_node_ids.append(n_id)
                
        for mcu_node_id in mcu_node_ids:
            # Extract connections for this MCU (UART, GPIOs, etc.)
            mcus_nodeconnect_in = reqdat[mcu_node_id].get('inputs', {})
            mcus_nodeconnect_out = reqdat[mcu_node_id].get('outputs', {})
            mcus_nodeconnect = {**mcus_nodeconnect_in, **mcus_nodeconnect_out}
            
            mcu_connected_devices = {}
            for port, port_data in mcus_nodeconnect.items():
                if port_data.get('connections'):
                    for conn in port_data['connections']:
                        conn_node_id = str(conn['node'])
                        if conn_node_id in id_device_mapping[email][project_name]:
                            conn_dev_name = id_device_mapping[email][project_name][conn_node_id]
                            # Store by port so we know if it's UART, GPIO, Camera etc.
                            if port not in mcu_connected_devices:
                                mcu_connected_devices[port] = []
                            mcu_connected_devices[port].append(conn_dev_name)
                            
            print(f"MCU {mcu_name} (Node {mcu_node_id}) connections: {mcu_connected_devices}")
            
            mcu_prompt = f"Generate Arduino (.ino) firmware skeleton for microcontroller {mcu_name}. "
            mcu_prompt += "Since there is no Single Board Computer, this system runs entirely on the MCU. "
            
            if "ESP32" in mcu_name.upper():
                mcu_prompt += "For this ESP32 module, strictly check the memory and flash space limitations of the specific ESP32 version. Ensure the generated code is optimized and fits within the usable memory footprint. "
                mcu_prompt += "If camera modules are connected, use the specific ESP32 Camera API. Do NOT use heavy vision libraries like OpenCV or YOLOv8, as they are not supported on this microcontroller. "
                
            mcu_prompt += f"The MCU is connected to the following components via specific ports (GPIO, UART, etc): {mcu_connected_devices}. "
            mcu_prompt += "Focus on utilizing UART and GPIO for communication rather than generic Serial intended for SBCs. "
            mcu_prompt += "Include necessary Arduino libraries (e.g., Wire.h, HardwareSerial). Leave the setup() and loop() structures, and create empty functions for reading sensors and writing actuator commands. Output ONLY the code, with no explanation."
            
            try:
                mcu_code_response = requests.post(SERVICE_URLS['gemini']+"/ask_gemini", json={"email":email, "project_name":project_name, "command": mcu_prompt}).json()[email]
                print(f"MCU Firmware Generated for {mcu_name}:\n", mcu_code_response)
                mcu_code_extracted = extract_code(mcu_code_response)
                firmware_dir = os.path.join("Client_code_generator", email, project_name, "firmware")
                os.makedirs(firmware_dir, exist_ok=True)
                with open(os.path.join(firmware_dir, f"{mcu_name}_firmware.ino"), "w") as f:
                    f.write(mcu_code_extracted)
                print(f"MCU Firmware saved to {firmware_dir}/{mcu_name}_firmware.ino")
            except Exception as e:
                print(f"Error generating MCU Firmware for {mcu_name}:", e)

    update_status(email, project_name, "complete")
    return {"status": "success", "message": "Code generation complete."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9057)    