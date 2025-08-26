# run_dashboard.py
#!/usr/bin/env python3
"""Runner script for Streamlit dashboard"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit dashboard"""
    try:
        # Make sure we're in the right directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        print("Starting Reddit Job Scraper Dashboard...")
        print("Dashboard will be available at: http://localhost:8501")
        print("Press Ctrl+C to stop the dashboard")
        
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--server.headless", "true"
        ])
        
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

