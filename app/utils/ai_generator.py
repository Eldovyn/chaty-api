import time
import base64
import urllib.parse
from typing import Optional, Dict, Any, Union, List
from google import genai
import requests
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from ..config import (
    gemini_api_key,
    imagekit_public_key,
    imagekit_private_key,
    imagekit_url_endpoint,
    default_folder,
)
import difflib
from werkzeug.datastructures import FileStorage


class ImageKitImageGenerator:
    def __init__(self) -> None:
        self.url_endpoint = (imagekit_url_endpoint or "").rstrip("/")
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

        try:
            resp = requests.get(generated_image_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            return None

        try:
            base64_image = base64.b64encode(resp.content).decode("utf-8")
        except Exception as e:
            return None

        try:
            upload_result = self.client.upload_file(
                file=base64_image,
                file_name=f"{ts}.png",
                options=UploadFileRequestOptions(folder=self.default_folder),
            )
        except Exception as e:
            return None

        image_url = getattr(upload_result, "url", None) or getattr(
            upload_result, "response_metadata", {}
        ).get("raw", {}).get("url")

        if image_url is None and isinstance(upload_result, dict):
            image_url = upload_result.get("url")

        return image_url


class GeminiAI:
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        timeout: float = 15.0,
    ):
        self.client = genai.Client(api_key=api_key or gemini_api_key)
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.timeout = timeout

    def generate_title_from_context(
        self,
        context: Union[str, List[str]],
        existing_titles: Optional[Union[str, List[str]]] = None,
        similarity_threshold: float = 0.8,
    ):
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

        generated_title = (response.text or "").strip()

        if not existing_titles:
            return generated_title

        if isinstance(existing_titles, str):
            existing_list = [existing_titles]
        else:
            existing_list = existing_titles

        def similarity(a: str, b: str) -> float:
            return difflib.SequenceMatcher(
                None, a.lower().strip(), b.lower().strip()
            ).ratio()

        for old in existing_list:
            sim = similarity(generated_title, old)
            if sim >= similarity_threshold:
                return old

        return generated_title

    def _safe_generate(
        self, contents, model: str = "gemini-2.5-flash"
    ) -> Optional[Any]:
        backoff = self.initial_backoff

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                )
                return response
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(backoff)
                    backoff *= 2

        return None

    def _safe_upload(self, file_input) -> Optional[Any]:
        backoff = self.initial_backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                uploaded = self.client.files.upload(file=file_input)
                return uploaded
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(backoff)
                    backoff *= 2

        return None

    def generate_sync(self, message: Union[str, List[str]]) -> str:
        resp = self._safe_generate(message, model="gemini-2.5-flash")
        if resp is None:
            return "Maaf, saat ini sistem AI sedang sibuk. Silakan coba lagi beberapa saat."
        return (resp.text or "").strip()

    def generate_title_from_context(
        self,
        context: Union[str, List[str]],
        existing_titles: Optional[Union[str, List[str]]] = None,
        similarity_threshold: float = 0.8,
    ):
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

        resp = self._safe_generate([prompt], model="gemini-2.0-flash")
        if resp is None:
            if existing_titles:
                if isinstance(existing_titles, str):
                    return existing_titles
                return existing_titles[0] if existing_titles else "Judul"
            return "Judul singkat tidak tersedia saat ini"

        generated_title = (resp.text or "").strip()
        if not existing_titles:
            return generated_title

        if isinstance(existing_titles, str):
            existing_list = [existing_titles]
        else:
            existing_list = existing_titles

        def similarity(a: str, b: str) -> float:
            return difflib.SequenceMatcher(
                None, a.lower().strip(), b.lower().strip()
            ).ratio()

        for old in existing_list:
            sim = similarity(generated_title, old)
            if sim >= similarity_threshold:
                return old

        return generated_title

    def get_prompt_mode(self, prompt: str) -> str:
        instruction = """
You are a classifier for user requests.

Decide whether the following user prompt is:
- IMAGE: user meminta untuk membuat / menggambar / menghasilkan gambar,
  ilustrasi, foto, icon, logo, poster, dsb.
- TEXT: user hanya bertanya atau meminta jawaban teks, tidak ingin dibuatkan gambar.

Jawab HANYA dengan salah satu kata berikut (huruf besar semua):
- IMAGE
- TEXT
"""
        resp = self._safe_generate(
            f"{instruction}\n\nPROMPT:\n{prompt}", model="gemini-2.5-flash"
        )
        if resp is None:
            return "TEXT"
        text = (resp.text or "").strip().upper()
        return "IMAGE" if text.startswith("IMAGE") else "TEXT"

    def is_valid_image_prompt(self, prompt: str) -> bool:
        instruction = """
You are a classifier for image generation prompts.

Decide whether the following user prompt is CLEAR and SPECIFIC enough
to be used for generating an image.

Answer with ONE WORD: VALID or INVALID.
"""
        resp = self._safe_generate(
            f"{instruction}\n\nPROMPT:\n{prompt}", model="gemini-2.5-flash"
        )
        if resp is None:
            return False
        text = (resp.text or "").strip().upper()
        return text.startswith("VALID")

    def prompt_requests_file_analysis(self, prompt: str) -> bool:
        if not prompt or not isinstance(prompt, str):
            return False

        instruction = """
You are a classifier. Decide whether the following user prompt explicitly or implicitly
requests analyzing, summarizing, or reading an uploaded document/file so that the
assistant should perform document analysis (e.g., "ringkas file", "summarize the attached file",
"what's in the document", "baca file ini", dsb).

Answer with ONE WORD ONLY: YES or NO.
If the prompt asks about unrelated questions (not about the uploaded file's content),
answer NO.
"""
        resp = self._safe_generate(
            f"{instruction}\n\nPROMPT:\n{prompt}", model="gemini-2.5-flash"
        )
        if resp is not None:
            text = (resp.text or "").strip().upper()
            first_word = text.split()[0] if text else ""
            if (
                first_word.startswith("Y")
                or first_word.startswith("YES")
                or first_word.startswith("YA")
            ):
                return True
            if (
                first_word.startswith("N")
                or first_word.startswith("NO")
                or first_word.startswith("TIDAK")
            ):
                return False

        p = prompt.lower()
        keywords = [
            "ringkas",
            "ringkasan",
            "ringkaskan",
            "buat ringkasan",
            "rangkum",
            "merangkum",
            "baca file",
            "baca dokumen",
            "jelaskan dokumen",
            "poin penting",
            "isi dokumen",
            "summarize",
            "summarise",
            "analyze the file",
            "analyze the document",
            "what is in the file",
            "what's in the file",
            "what's in the document",
        ]
        return any(k in p for k in keywords)

    def analyze_document(
        self,
        file_input: Union[str, bytes],
        instruction: str = (
            "Ringkas isi dokumen ini dan jelaskan poin-poin pentingnya dalam bahasa Indonesia."
        ),
    ) -> Dict[str, Any]:
        uploaded_file = self._safe_upload(file_input)
        if uploaded_file is None:
            return {
                "is_image": False,
                "content": "Gagal mengunggah dokumen untuk dianalisis. Silakan coba lagi nanti.",
            }

        resp = self._safe_generate(
            [instruction, uploaded_file], model="gemini-2.5-flash"
        )
        if resp is None:
            return {
                "is_image": False,
                "content": "Saat ini aku belum bisa menganalisis dokumen tersebut. Silakan coba lagi nanti.",
            }
        text = (resp.text or "").strip()
        return {"is_image": False, "content": text}

    def handle_image_prompt(
        self,
        prompt: str,
        image_generator: ImageKitImageGenerator,
        referenced_file: Union[None, str, bytes] = None,
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
            return {"is_image": False, "content": answer}

        if not self.is_valid_image_prompt(prompt):
            fallback_prompt = f"""
Pengguna mengirim pesan berikut:

\"\"\"{prompt}\"\"\"

Prompt ini belum cukup jelas untuk membuat gambar. Tolong minta mereka menjelaskan objek, suasana, gaya, warna, dan detail lain secara singkat.
"""
            fallback_text_resp = self._safe_generate(
                fallback_prompt, model="gemini-2.5-flash"
            )
            fallback_text = (
                (fallback_text_resp.text or "").strip()
                if fallback_text_resp
                else (
                    "Maaf, prompt kurang jelas. Tolong jelaskan objek, suasana, gaya, warna, dan detail lain secara singkat."
                )
            )
            return {"is_image": False, "content": fallback_text}

        try:
            image_url = image_generator.generate_image(prompt)
        except Exception as e:
            print(f"[GeminiAI] image generation error: {e}")
            image_url = None

        if image_url:
            return {"is_image": True, "content": image_url}

        fallback_prompt = f"""
Pengguna mengirim permintaan untuk membuat gambar dengan prompt:

\"\"\"{prompt}\"\"\"

Namun sistem tidak dapat membuat gambar tersebut sekarang.
"""
        fallback_text_resp = self._safe_generate(
            fallback_prompt, model="gemini-2.5-flash"
        )
        fallback_text = (
            (fallback_text_resp.text or "").strip()
            if fallback_text_resp
            else (
                "Maaf, saat ini sistem belum bisa membuat gambar. Silakan coba lagi nanti atau kirim prompt lain."
            )
        )
        return {"is_image": False, "content": fallback_text}

    def handle_request(
        self,
        prompt: Optional[str],
        image_generator: ImageKitImageGenerator,
        file_input: Union[None, str, bytes] = None,
        instruction_for_doc: str = (
            "Ringkas isi dokumen ini dan jelaskan poin-poin pentingnya dalam bahasa Indonesia."
        ),
    ) -> Dict[str, Any]:
        """
        Flow utama sesuai permintaan:
        1) Jika prompt meminta IMAGE -> generate gambar (abaikan file_input).
        2) Jika prompt TEXT dan meminta analisis file -> analisis dokumen (hanya jika file_input tersedia).
        3) Jika prompt TEXT dan tidak meminta analisis file -> jawab teks (abaikan file_input).
        4) Jika tidak ada prompt tapi ada file_input -> analisis dokumen.
        5) Kalau tidak ada apa-apa -> minta input user.
        """
        prompt = (prompt or "").strip()

        if prompt:
            mode = self.get_prompt_mode(prompt)
            if mode == "IMAGE":
                return self.handle_image_prompt(prompt, image_generator)

            if self.prompt_requests_file_analysis(prompt):
                if file_input is not None:
                    return self.analyze_document(
                        file_input=file_input, instruction=instruction_for_doc
                    )
                else:
                    return {
                        "is_image": False,
                        "content": "Kamu meminta ringkasan/analisis, tapi belum mengunggah dokumen. Silakan unggah file atau kirim teksnya.",
                    }

            answer = self.generate_sync(prompt)
            return {"is_image": False, "content": answer}

        if file_input is not None:
            return self.analyze_document(
                file_input=file_input, instruction=instruction_for_doc
            )

        return {
            "is_image": False,
            "content": "Tolong tuliskan pertanyaan, perintah, atau unggah dokumen yang ingin dianalisis.",
        }
