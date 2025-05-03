import os
import openai
from typing import Optional


class ChatGPTService:
    def __init__(self, config_model_name: Optional[str] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            print("WARNING: ChatGPTService initialized, but OPENAI_API_KEY is missing!")

        default_model = 'gpt-4o-mini'
        self.model_name = config_model_name if config_model_name else default_model
        print(f"INFO: ChatGPTService using model: {self.model_name}")

        if not self.api_key:
            self.client = None
        else:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                self.client = None

    def is_ready(self):
        if self.client is None:
            if not self.api_key:
                print("Warning: OpenAI API key not found. ChatGPT service disabled.")
            else:
                print("Warning: OpenAI client failed to initialize. ChatGPT service likely disabled.")
            return False
        return True

    def __execute_chat_completion(self, model, messages, temperature, max_tokens):
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def get_project_ideas(self, prompt):
        if not self.is_ready():
            return "Error: ChatGPT service is not configured or failed to initialize."

        try:
            response = self.__execute_chat_completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            if response.choices:
                return response.choices[0].message.content.strip()
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
        except openai.OpenAIError as e:
            print(f"An OpenAI error occurred during ChatGPT request: {e}")
            return f"An OpenAI error occurred: {e}"
        except Exception as e:
            print(f"An unexpected error occurred during ChatGPT request: {e}")
            return f"An unexpected error occurred: {e}"
