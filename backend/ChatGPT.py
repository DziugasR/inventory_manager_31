import os
import openai
from dotenv import load_dotenv
import configparser

class ChatGPTService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")

        config = configparser.ConfigParser()
        config_path = 'config.ini'
        default_model = 'gpt-4o-mini'
        self.model_name = default_model

        try:
            if config.read(config_path):
                self.model_name = config.get('OpenAI', 'model', fallback=default_model)
            else:
                print(f"Warning: Configuration file '{config_path}' not found or empty. Using default OpenAI model: {self.model_name}")
        except configparser.Error as e:
            print(f"Error reading configuration file '{config_path}': {e}. Using default OpenAI model: {self.model_name}")
        except Exception as e:
             print(f"Unexpected error reading config file '{config_path}': {e}. Using default OpenAI model: {self.model_name}")

        print(f"INFO: Using OpenAI model: {self.model_name}")

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
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            if response.choices:
                generated_text = response.choices[0].message.content.strip()
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
        except openai.OpenAIError as e:
            print(f"An OpenAI error occurred during ChatGPT request: {e}")
            return f"An OpenAI error occurred: {e}"
        except Exception as e:
            print(f"An unexpected error occurred during ChatGPT request: {e}")
            return f"An unexpected error occurred: {e}"