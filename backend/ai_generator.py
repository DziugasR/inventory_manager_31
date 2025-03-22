# import openai
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#
# openai.api_key = OPENAI_API_KEY
#
# def generate_project_ideas(component_name):
#     """ Uses ChatGPT to generate project ideas based on a component. """
#     prompt = f"Suggest three creative project ideas using a {component_name}."
#
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "system", "content": prompt}]
#         )
#         return response['choices'][0]['message']['content']
#     except Exception as e:
#         return f"Error generating ideas: {e}"
