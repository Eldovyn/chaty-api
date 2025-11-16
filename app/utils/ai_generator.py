import time
import base64
import urllib.parse
from typing import Optional, Dict, Any, Union, List
from google import genai
import requests
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from google.genai import types as genai_types
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

    # =========================
    # Helper: jawaban teks biasa
    # =========================
    def generate_sync(self, message: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message,
        )
        return (response.text or "").strip()

    # =========================
    # Klasifikasi: IMAGE vs TEXT
    # =========================
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

    # =========================
    # Validasi prompt gambar
    # =========================
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

    # =========================
    # Handler: prompt text -> TEXT / IMAGE
    # =========================
    def handle_image_prompt(
        self,
        prompt: str,
        image_generator: ImageKitImageGenerator,
    ) -> Dict[str, Any]:
        """
        - Kalau user cuma bertanya/teks → jawab teks (is_image=False).
        - Kalau user minta gambar → validasi prompt → generate via ImageKit.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return {
                "is_image": False,
                "content": "Tolong tuliskan deskripsi atau pertanyaanmu.",
            }

        mode = self.get_prompt_mode(prompt)

        # Hanya bertanya / ingin jawaban teks → langsung generate_sync
        if mode == "TEXT":
            answer = self.generate_sync(prompt)
            return {
                "is_image": False,
                "content": answer,
            }

        # User memang minta gambar → validasi deskripsi
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

        # Prompt valid → generate image ke ImageKit
        image_url = image_generator.generate_image(prompt)

        if image_url:
            return {
                "is_image": True,
                "content": image_url,
            }

        # Gagal generate / upload → fallback teks
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

    # =========================
    # Handler: analisis dokumen (PDF/CSV/Word)
    # =========================
    def analyze_document(
        self,
        file_input: Union[str, bytes],  # path string ATAU bytes
        filename: str,
        mime_type: str,
        instruction: str = "Ringkas isi dokumen ini dan jelaskan poin-poin pentingnya dalam bahasa Indonesia.",
    ) -> Dict[str, Any]:
        """
        Analisis dokumen (PDF/CSV/Word, dll) dengan Gemini.

        - file_input : path string (mis. './file.pdf') ATAU bytes (mis. file.read()).
        - filename   : nama file untuk display.
        - mime_type  : mimetype file (application/pdf, text/csv, application/vnd.openxmlformats-officedocument.wordprocessingml.document, dll).
        - instruction: instruksi ke Gemini.

        Return:
        {
          "is_image": False,
          "content": "<hasil analisis (teks)>"
        }
        """

        # 1. Upload file ke Gemini File API
        try:
            uploaded_file = self.client.files.upload(
                file=file_input,
                config=genai_types.UploadFileConfig(
                    display_name=filename,
                    mime_type=mime_type,
                ),
            )
        except Exception as e:
            fallback = (
                "Gagal mengunggah dokumen untuk dianalisis. "
                "Silakan coba lagi atau unggah file lain. "
                f"Detail teknis: {e}"
            )
            return {
                "is_image": False,
                "content": fallback,
            }

        # 2. Panggil model dengan file + instruction
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    instruction,  # instruksi teks
                    uploaded_file,  # referensi file
                ],
            )
            text = (response.text or "").strip()
        except Exception as e:
            text = (
                "Saat ini aku belum bisa menganalisis dokumen tersebut. "
                "Silakan coba lagi nanti. "
                f"Detail teknis: {e}"
            )

        return {
            "is_image": False,
            "content": text,
        }

    # =========================
    # ENTRY POINT UTAMA
    # =========================
    def handle_request(
        self,
        prompt: Optional[str],
        image_generator: ImageKitImageGenerator,
        file_input: Union[None, str, bytes] = None,
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        instruction_for_doc: str = "Ringkas isi dokumen ini dan jelaskan poin-poin pentingnya dalam bahasa Indonesia.",
    ) -> Dict[str, Any]:
        """
        Satu pintu:
        - Kalau ada file_input  -> analisis dokumen
        - Kalau tidak ada file  -> handle_image_prompt (Q&A / generate image)

        Return shape:
        {
          "is_image": bool,
          "content": "<teks atau url gambar>"
        }
        """

        # CASE 1: ada dokumen yang mau dianalisis
        if file_input is not None and filename and mime_type:
            return self.analyze_document(
                file_input=file_input,
                filename=filename,
                mime_type=mime_type,
                instruction=instruction_for_doc,
            )

        # CASE 2: tidak ada file → gunakan alur prompt biasa
        prompt = (prompt or "").strip()
        if not prompt:
            return {
                "is_image": False,
                "content": "Tolong tuliskan pertanyaan, perintah, atau unggah dokumen yang ingin dianalisis.",
            }

        return self.handle_image_prompt(prompt, image_generator)
