from email_validator import validate_email
import re
from ..config import provider as PROVIDER
from .token import (
    TokenAccountActive,
    TokenResetPassword,
)


class Validation:
    @staticmethod
    async def validate_email(errors, email):
        if email is None or (isinstance(email, str) and email.strip() == ""):
            errors.setdefault("email", []).append("IS_REQUIRED")
        else:
            if not isinstance(email, str):
                errors.setdefault("email", []).append("MUST_TEXT")
            if isinstance(email, str) and len(email) < 5:
                errors.setdefault("email", []).append("TOO_SHORT")
            if isinstance(email, str) and len(email) > 50:
                errors.setdefault("email", []).append("TOO_LONG")
            try:
                valid = validate_email(email)
                email = valid.email
            except:
                errors.setdefault("email", []).append("IS_INVALID")
        return errors

    @staticmethod
    async def validate_username(errors, username):
        if username is None or (isinstance(username, str) and username.strip() == ""):
            errors.setdefault("username", []).append("IS_REQUIRED")
        else:
            if not isinstance(username, str):
                errors.setdefault("username", []).append("MUST_TEXT")
            if isinstance(username, str) and len(username) < 3:
                errors.setdefault("username", []).append("TOO_SHORT")
            if isinstance(username, str) and len(username) > 30:
                errors.setdefault("username", []).append("TOO_LONG")
        return errors

    @staticmethod
    async def validate_password(errors, password, confirm_password):
        if password is None or (isinstance(password, str) and password.strip() == ""):
            errors.setdefault("password", []).append("IS_REQUIRED")
        else:
            if not isinstance(password, str):
                errors.setdefault("password", []).append("MUST_TEXT")
        if not confirm_password or (
            isinstance(confirm_password, str) and confirm_password.isspace()
        ):
            errors.setdefault("confirm_password", []).append("IS_REQUIRED")
        else:
            if not isinstance(confirm_password, str):
                errors.setdefault("confirm_password", []).append("MUST_TEXT")
        if password != confirm_password and (
            password or (isinstance(password, str) and not password.isspace())
        ):
            errors.setdefault("password_match", []).append("IS_MISMATCH")
        if isinstance(password, str) and password == confirm_password:
            if len(password) > 64:
                errors.setdefault("password_security", []).append("TOO_LONG")
            if len(password) < 8:
                errors.setdefault("password_security", []).append("TOO_SHORT")
            if not re.search(r"[A-Z]", password):
                errors.setdefault("password_security", []).append("NO_CAPITAL")
            if not re.search(r"[a-z]", password):
                errors.setdefault("password_security", []).append("NO_LOWERCASE")
            if not re.search(r"[0-9]", password):
                errors.setdefault("password_security", []).append("NO_NUMBER")
            if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
                errors.setdefault("password_security", []).append("NO_SYMBOL")
            if not re.search(r"[A-Za-z]", password):
                errors.setdefault("password_security", []).append("NO_LETTER")

    @staticmethod
    async def validate_provider(errors, provider):
        if provider is None or (isinstance(provider, str) and provider.strip() == ""):
            errors.setdefault("provider", []).append("IS_REQUIRED")
        else:
            if not isinstance(provider, str):
                errors.setdefault("provider", []).append("MUST_TEXT")
            if provider not in PROVIDER.split(", "):
                errors.setdefault("provider", []).append("IS_INVALID")
        return errors

    @staticmethod
    async def validate_required_text(errors, field_name, value):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors.setdefault(field_name, []).append("IS_REQUIRED")
        else:
            if not isinstance(value, str):
                errors.setdefault(field_name, []).append("MUST_TEXT")

    @staticmethod
    async def validate_otp(errors, otp):
        if otp is None or (isinstance(otp, str) and otp.strip() == ""):
            errors.setdefault("otp", []).append("IS_REQUIRED")
        else:
            if not isinstance(otp, str):
                errors.setdefault("otp", []).append("MUST_TEXT")
            if len(otp) < 0 or len(otp) > 4:
                errors.setdefault("otp", []).append("IS_INVALID")

    @staticmethod
    async def validate_token(errors, token, category):
        if category == "token_account_active":
            if not (token_account_active := await TokenAccountActive.get(token)):
                errors.setdefault("token", []).append("IS_INVALID")
        elif category == "token_reset_password":
            if not (token_reset_password := await TokenResetPassword.get(token)):
                errors.setdefault("token", []).append("IS_INVALID")
        return errors
