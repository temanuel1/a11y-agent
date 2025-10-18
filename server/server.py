import subprocess
import time
import json
import os


def run_lighthouse_analysis(port=5173):
    """
    Starts Vite dev server and runs Lighthouse analysis.
    Returns lighthouse results as dict.
    """
    server_process = None
    
    try:
        # Start Vite dev server
        print(f"Starting Vite dev server on port {port}...")
        server_process = subprocess.Popen(
            ["npx", "vite", "--port", str(port)],
            cwd=os.path.join(os.path.dirname(__file__), "template"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to be ready
        print("Waiting for server to start...")
        time.sleep(3)  # Give it time to start
        
        # Run Lighthouse
        print("Running Lighthouse analysis...")
        lighthouse_output_path = os.path.join(os.path.dirname(__file__), "lighthouse-results.json")
        
        lighthouse_process = subprocess.run(
            [
                "npx", "lighthouse",
                f"http://localhost:{port}",
                "--output=json",
                f"--output-path={lighthouse_output_path}",
                "--only-categories=accessibility",
                "--chrome-flags=--headless"
            ],
            capture_output=True,
            text=True
        )
        
        if lighthouse_process.returncode != 0:
            print(f"Lighthouse error: {lighthouse_process.stderr}")
            return None
        
        # Read results
        with open(lighthouse_output_path, "r") as f:
            results = json.load(f)
        
        print("Lighthouse analysis complete!")
        return results
        
    except Exception as e:
        print(f"Error during lighthouse analysis: {e}")
        return None
        
    finally:
        # Clean up server process
        if server_process:
            print("Shutting down server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

