from flask import Blueprint, request
from ..controllers import (
    LoginController,
    AccountActiveController,
    OtpEmailController,
    RegisterController,
    ResetPasswordController,
)
from ..utils import jwt_required

auth_router = Blueprint("auth_router", __name__)
login_controller = LoginController()
account_active_controller = AccountActiveController()
otp_email_controller = OtpEmailController()
register_controller = RegisterController()
reset_password_controller = ResetPasswordController()


@auth_router.post("/login")
async def user_login():
    data = request.json
    timestamp = request.timestamp
    email = data.get("email", "")
    password = data.get("password", "")
    provider = data.get("provider", "")
    token = data.get("token", "")
    return await login_controller.user_login(
        provider, token, email, password, timestamp
    )


@auth_router.post("/register")
async def user_register():
    data = request.json
    timestamp = request.timestamp
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    provider = data.get("provider", "")
    token = data.get("token", "")
    return await register_controller.user_register(
        provider,
        token,
        username,
        email,
        password,
        confirm_password,
        timestamp,
    )


@auth_router.post("/logout")
@jwt_required()
async def user_logout():
    user = request.user
    token = request.token
    return await login_controller.user_logout(user, token)


@auth_router.post("/reset-password/request")
async def send_reset_password_email():
    data = request.json
    timestamp = request.timestamp
    email = data.get("email", "")
    return await reset_password_controller.send_reset_password_email(email, timestamp)


@auth_router.get("/reset-password/password-changed/<string:token>")
async def get_user_reset_password_verification(token):
    timestamp = request.timestamp
    return await reset_password_controller.get_user_reset_password_verification(
        token, timestamp
    )


@auth_router.post("/reset-password/password-changed/<string:token>")
async def user_reset_password_verification(token):
    timestamp = request.timestamp
    json = request.json
    confirm_password = json.get("confirm_password", "")
    password = json.get("password", "")
    return await reset_password_controller.user_reset_password_verification(
        token, password, confirm_password, timestamp
    )


@auth_router.post("/account-active/request")
async def send_account_active_email():
    data = request.json
    timestamp = request.timestamp
    email = data.get("email", "")
    return await account_active_controller.send_account_active_email(email, timestamp)


@auth_router.get("/account-active/<string:user_id>")
async def get_token_by_user_id(user_id):
    timestamp = request.timestamp
    return await account_active_controller.get_token_by_user_id(user_id, timestamp)


@auth_router.get("/account-active/activation/<string:token>")
async def get_user_account_active_verification(token):
    timestamp = request.timestamp
    return await account_active_controller.get_user_account_active_verification(
        token, timestamp
    )


@auth_router.post("/account-active/activation/<string:token>")
async def user_account_active_verification(token):
    json = request.json
    otp = json.get("otp", "")
    timestamp = request.timestamp
    return await account_active_controller.user_account_active_verification(
        token, otp, timestamp
    )


@auth_router.post("/account-active/activation/<string:token>/re-send")
async def user_account_active_verification_re_send(token):
    timestamp = request.timestamp
    return await account_active_controller.user_account_active_verification_re_send(
        token, timestamp
    )


@auth_router.post("/otp/email")
@jwt_required()
async def otp_email():
    user = request.user
    timestamp = request.timestamp
    return await otp_email_controller.otp_email(user, timestamp)
