import re
import json
from datetime import datetime, timezone
from filelock import Timeout, FileLock

import sys
sys.path.append('..')
from UserManagement.UserManager import UserManager

class ResponseParser:
    def __init__(self):
        self.user_manager = UserManager()
        self.response_file = "summary_data.json"
        self.lock_path = "summary_data.lock"
        self.lock = FileLock(self.lock_path, timeout=2)

    def create_response_file(self):
        try:
            with open(self.response_file, "w") as file:
                json.dump({}, file)
        except Exception as e:
            print(f"Error creating response file: {e}")

    def get_current_user_id(self):
        current_user = self.user_manager.get_curr_user()
        if current_user:
            return current_user["username"]
        return None

    def save_response(self, response):
        user_id = self.get_current_user_id()
        if not user_id:
            print("No current user found.")
            return

        try:
            with self.lock.acquire(timeout=2):
                with open(self.response_file, "r+") as file:
                    data = json.load(file)
                    current_time_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
                    if user_id not in data:
                        data[user_id] = [{"response": response, "timestamp": current_time_utc}]
                    else:
                        user_responses = data[user_id]
                        if len(user_responses) >= 10:
                            user_responses.pop(0)  # Remove oldest response
                        user_responses.append({"response": response, "timestamp": current_time_utc})
                        data[user_id] = user_responses
                    file.seek(0)
                    json.dump(data, file)
                    file.truncate()
                    print("Response saved successfully.")
        except Timeout:
            print("Another instance of this application currently holds the lock.")
        except Exception as e:
            print(f"Error saving response: {e}")

    def remove_markdown(self, response):
        markdown_pattern = r'(\*{2})(.*?)\1|\*(.*?)\*|#{1,6}\s*'
        cleaned_response = re.sub(markdown_pattern, r'\2\3', response)

        return cleaned_response

# Example usage
if __name__ == "__main__":
    parser = ResponseParser()
    try:
        with open(parser.response_file, "r"):
            pass
    except FileNotFoundError:
        parser.create_response_file()

    user_manager = UserManager()

    user_manager.store_user_data(
        username="JohnDoe",
        email="john@example.com",
        password="password123",
        gemini_api_key="gemini_api_key_value",
        openai_api_key="openai_api_key_value",
        slack_email="john@slack.com",
        slack_id="U12345678"
    )

    user_manager.login("JohnDoe", "password123")
    print(user_manager.get_keys())
    print(user_manager.get_curr_user())

    response = "This is *italic* and **bold** text."
    cleaned_response = parser.remove_markdown(response)
    parser.save_response(cleaned_response)

    user_manager.logout()