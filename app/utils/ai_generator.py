import time
import base64
import urllib.parse
from typing import Optional, Dict, Any
from google import genai
import requests
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from typing import Union, List
from ..config import (
    gemini_api_key,
    imagekit_public_key,
    imagekit_private_key,
    imagekit_url_endpoint,
    default_folder,
)


class ImageKitImageGenerator:
    def __init__(
        self,
    ) -> None:
        self.url_endpoint = imagekit_url_endpoint.rstrip("/")
        self.default_folder = default_folder

        self.client = ImageKit(
            public_key=imagekit_public_key,
            private_key=imagekit_private_key,
            url_endpoint=imagekit_url_endpoint,
        )

    def generate_image(
        self, prompt: str, width: int = 800, height: int = 800
    ) -> Optional[str]:
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("Prompt tidak boleh kosong")

        encoded_prompt = urllib.parse.quote(prompt, safe="")

        ts = int(time.time() * 1000)

        generated_image_url = (
            f"{self.url_endpoint}"
            f"/ik-genimg-prompt-{encoded_prompt}/ai-gen/{ts}.png"
            f"?tr=w-{width},h-{height}"
        )

        resp = requests.get(generated_image_url)
        try:
            resp.raise_for_status()
        except Exception:
            return None

        base64_image = base64.b64encode(resp.content).decode("utf-8")

        try:
            upload_result = self.client.upload_file(
                file=base64_image,
                file_name=f"{ts}.png",
                options=UploadFileRequestOptions(folder=self.default_folder),
            )
        except Exception:
            return None

        image_url = getattr(upload_result, "url", None) or getattr(
            upload_result, "response_metadata", {}
        ).get("raw", {}).get("url")

        if image_url is None and isinstance(upload_result, dict):
            image_url = upload_result.get("url")

        return image_url


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

    def generate_sync(self, message: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message,
        )
        return (response.text or "").strip()

    def get_prompt_mode(self, prompt: str) -> str:
        instruction = """
        You are a classifier for user requests.

        Decide whether the following user prompt is:
        - IMAGE: user meminta untuk membuat / menggambar / menghasilkan gambar,
          ilustrasi, foto, icon, logo, poster, dsb.
        - TEXT: user hanya bertanya atau meminta jawaban teks, tidak ingin dibuatkan gambar.

        Contoh yang termasuk IMAGE:
        - "buatkan ilustrasi kucing lucu"
        - "tolong generate gambar rumah di pegunungan"
        - "bikinin logo simple warna biru"
        - "create an image of a robot in cyberpunk style"

        Contoh yang termasuk TEXT:
        - "siapa presiden indonesia pertama"
        - "jelaskan teori relativitas"
        - "tuliskan puisi tentang hujan"
        - "apa itu machine learning"

        Jawab HANYA dengan salah satu kata berikut (huruf besar semua):
        - IMAGE
        - TEXT
        """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{instruction}\n\nPROMPT:\n{prompt}",
        )
        text = (response.text or "").strip().upper()

        return "IMAGE" if text.startswith("IMAGE") else "TEXT"

    def is_valid_image_prompt(self, prompt: str) -> bool:
        instruction = """
        You are a classifier for image generation prompts.

        Decide whether the following user prompt is CLEAR and SPECIFIC enough
        to be used for generating an image.

        Rules:
        - VALID if: mengandung deskripsi visual yang cukup jelas
          (mis. objek, suasana, warna, gaya, aksi, dll).
        - INVALID if: terlalu pendek dan ambigu (misal "dsadasda"),
          hanya berupa pertanyaan non-visual (misal "apa kabar?"),
          atau tidak mengandung apapun yang bisa divisualisasikan dengan wajar.

        Jawab HANYA dengan salah satu kata berikut (huruf besar semua):
        - VALID
        - INVALID
        """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{instruction}\n\nPROMPT:\n{prompt}",
        )
        text = (response.text or "").strip().upper()
        return text.startswith("VALID")

    def handle_image_prompt(
        self,
        prompt: str,
        image_generator: ImageKitImageGenerator,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            return {
                "is_image": False,
                "content": "Tolong tuliskan deskripsi atau pertanyaanmu.",
            }

        mode = self.get_prompt_mode(prompt)

        if mode == "TEXT":
            answer = self.generate_sync(prompt)
            return {
                "is_image": False,
                "content": answer,
            }

        if not self.is_valid_image_prompt(prompt):
            fallback_prompt = f"""
            Pengguna mengirim pesan berikut:

            \"\"\"{prompt}\"\"\"

            Prompt ini belum cukup jelas atau kurang cocok untuk dibuatkan gambar.
            Balas pengguna dalam 1–2 kalimat singkat berbahasa Indonesia yang sopan,
            minta mereka untuk menjelaskan ulang atau memberikan deskripsi gambar yang
            lebih spesifik (misalnya objek apa, suasananya bagaimana, gaya apa, dll).

            Jangan sebut soal validasi, model, atau error teknis. 
            Jawab hanya isi chat ke user, tanpa penjelasan tambahan.
            """
            fallback_text = self.generate_sync(fallback_prompt)

            return {
                "is_image": False,
                "content": fallback_text,
            }

        image_url = image_generator.generate_image(prompt)

        if image_url:
            return {
                "is_image": True,
                "content": image_url,
            }

        fallback_prompt = f"""
        Pengguna mengirim permintaan untuk membuat gambar dengan prompt:

        \"\"\"{prompt}\"\"\"

        Namun sistem tidak dapat membuat gambar tersebut.
        Buat satu kalimat singkat dalam bahasa Indonesia yang menjelaskan bahwa
        saat ini kamu belum bisa membuat gambar, dan minta pengguna untuk mencoba lagi
        beberapa saat lagi atau mengirim prompt lain.

        Jangan sebut alasan teknis atau error server.
        Jawab hanya isi chat ke user, tanpa penjelasan tambahan.
        """

        fallback_text = self.generate_sync(fallback_prompt)

        return {
            "is_image": False,
            "content": fallback_text,
        }
