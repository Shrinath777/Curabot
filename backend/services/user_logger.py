import os
import pandas as pd
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_logs.xlsx")

def log_user_action(action_type: str, email: str, full_name: str):
    """
    Log user actions (signup, login) to an Excel file.
    NOTE: Never log passwords or sensitive credentials.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = {
        "Timestamp": timestamp,
        "Action": action_type,
        "Full Name": full_name or "N/A",
        "Email": email,
    }
    
    df_new = pd.DataFrame([new_entry])
    
    if os.path.exists(LOG_FILE):
        try:
            df_existing = pd.read_excel(LOG_FILE)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(LOG_FILE, index=False)
        except Exception as e:
            print(f"Error appending to Excel: {e}")
            # If corrupted, overwrite with the new one just to be safe
            df_new.to_excel(LOG_FILE, index=False)
    else:
        df_new.to_excel(LOG_FILE, index=False)
