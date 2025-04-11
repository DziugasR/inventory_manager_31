import os
import openai
from dotenv import load_dotenv

class ChatGPTService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            print("Warning: OPENAI_API_KEY environment variable not set.")
            self.client = None
        else:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print("ChatGPT Service Initialized.")
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                self.client = None

    def is_ready(self):
        return self.client is not None

    def get_project_ideas(self, prompt):
        if not self.is_ready():
            return "Error: ChatGPT service is not configured (API key missing or invalid)."

        try:
            print(f"Sending prompt to ChatGPT:\n---\n{prompt}\n---")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            if response.choices:
                generated_text = response.choices[0].message.content.strip()
                print("ChatGPT Response Received.")
                return generated_text
            else:
                return "Error: No response choices received from ChatGPT."

        except openai.AuthenticationError:
             print("Error: OpenAI Authentication Failed. Check your API key.")
             return "Error: OpenAI Authentication Failed. Invalid API key?"
        except openai.RateLimitError:
            print("Error: OpenAI Rate Limit Exceeded. Please try again later.")
            return "Error: OpenAI Rate Limit Exceeded. Try again later."
        except openai.APIConnectionError as e:
            print(f"Error: OpenAI API Connection Error: {e}")
            return f"Error: Could not connect to OpenAI API."
        except Exception as e:
            print(f"An unexpected error occurred during ChatGPT request: {e}")
            return f"An unexpected error occurred: {e}"