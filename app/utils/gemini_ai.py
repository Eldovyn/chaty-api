from google import genai
from ..config import gemini_api_key


class GeminiAI:
    def __init__(self):
        self.client = genai.Client(api_key=gemini_api_key)

    async def generate_async(self, message):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash", contents=message
        )
        return response.text

    def generate_sync(self, message):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash", contents=message
        )
        return response.text
