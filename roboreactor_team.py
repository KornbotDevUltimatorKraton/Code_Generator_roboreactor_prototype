import time
import requests
import os

EMAIL = "kornbot380@hotmail.com"  # Default email to monitor
DEFAULT_PROJECT_NAME = "Smart_Robots"  # Default fallback project name
BASE_URL = "http://roboreactor.com"

def main():
    print("=========================================================")
    print("Starting Roboreactor Team Automatic Code Downloader Agent")
    print("=========================================================")
    downloaded_projects = {} # Tracks state to prevent infinite loops of downloading the same file.

    while True:
        try:
            # 1. Dynamically try to get current active project details
            email = EMAIL
            project_name = None
            try:
                # Retrieve the currently active project registration (Assuming this endpoint is also available publicly)
                # If not available publicly, we'll fall back to default
                res = requests.get(f"{BASE_URL}/current_project", timeout=2.0).json()
                if res:
                    email = list(res.keys())[0]
                    project_name = res[email]['project_name']
            except Exception:
                project_name = DEFAULT_PROJECT_NAME

            # 2. Poll the toggle trigger status from the public domain
            status_url = f"{BASE_URL}/export_trigger_status"
            resp = requests.post(status_url, json={"email": email, "project_name": project_name}, timeout=5.0)
            
            if resp.status_code == 200:
                status_data = resp.json()
                trigger_status = status_data.get("status")

                if trigger_status == "ON":
                    print(f"\n[ALERT] Code generation trigger is ON for project '{project_name}' under '{email}'!")
                    print("Initiating automatic package download from roboreactor.com...")
                    
                    download_url = f"{BASE_URL}/download_generated_code"
                    dl_resp = requests.post(download_url, json={"email": email, "project_name": project_name}, stream=True, timeout=30.0)
                    
                    if dl_resp.status_code == 200:
                        filename = f"{project_name}_generated_code.zip"
                        with open(filename, 'wb') as f:
                            for chunk in dl_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"[SUCCESS] Download completed! Saved package as: {filename}")
                        # Note: Server automatically sets status to "OFF" when we download it, so we don't need local locking
                    else:
                        print(f"[ERROR] Failed downloading code from main server: HTTP {dl_resp.status_code}")

        except Exception as e:
            print("Error encountered in loop iteration:", e)

        time.sleep(3.0)

if __name__ == "__main__":
    main()
