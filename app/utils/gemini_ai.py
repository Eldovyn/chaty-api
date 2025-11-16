from google import genai
from ..config import gemini_api_key
from typing import Union, List


class GeminiAI:
    def __init__(self):
        self.client = genai.Client(api_key=gemini_api_key)

    def generate_title_from_context(self, context: Union[str, List[str]]):
        if isinstance(context, list):
            joined_context = "\n\n".join(str(c) for c in context)
        else:
            joined_context = str(context)

        prompt = f"""
        Kamu adalah asisten yang ahli merangkum.
        Buat satu judul yang singkat, jelas, dan menarik (maksimal 12 kata)
        untuk teks berikut ini. Jawab hanya dengan judulnya saja, tanpa penjelasan lain.

        Teks:
        \"\"\"{joined_context}\"\"\"
        """

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
        )

        title = (response.text or "").strip()
        return title

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
