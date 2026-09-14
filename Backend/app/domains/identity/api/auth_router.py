   
from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Cookie, Form, Request, Response
from fastapi.responses import HTMLResponse

from app.domains.identity.api.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    PasswordResetRequestResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegistrationPendingResponse,
    ResetPasswordRequest,
    make_token_response,
    map_org_to_response,
    map_user_to_response,
)
from app.domains.identity.application.auth_service import AuthService
from app.domains.identity.application.commands import (
    LoginCommand,
    LogoutCommand,
    RefreshTokensCommand,
    RegisterOrgCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
)
from app.domains.identity.application.queries import GetMeQuery
from app.domains.identity.application.user_service import UserService
from app.domains.identity.infra.repositories import (
    SQLOrganizationRepository,
    SQLPendingUserRepository,
    SQLRefreshTokenRepository,
    SQLUserRepository,
)
from app.shared.config import settings
from app.shared.deps import CurrentUser, DBSession
from app.shared.exceptions import InvalidTokenError
from app.shared.workers.notification_tasks import send_notification
from app.domains.notifications.infra.email_adapter import EmailAdapter

router = APIRouter(prefix="/auth", tags=["Authentication"])

                      
_COOKIE_NAME = "df_refresh"
_COOKIE_PATH = "/api/v1/identity/auth"
_COOKIE_MAX_AGE = settings.refresh_token_expire_seconds


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
                                                                               
    response.set_cookie(
        key=_COOKIE_NAME,
        value=raw_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.is_production,                             
        samesite="lax",                                   
        path=_COOKIE_PATH,                                         
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path=_COOKIE_PATH)


def _build_auth_service(db) -> AuthService:
    return AuthService(
        user_repo=SQLUserRepository(db),
        org_repo=SQLOrganizationRepository(db),
        token_repo=SQLRefreshTokenRepository(db),
        pending_user_repo=SQLPendingUserRepository(db),
    )


def _build_user_service(db) -> UserService:
    return UserService(
        user_repo=SQLUserRepository(db),
        org_repo=SQLOrganizationRepository(db),
        token_repo=SQLRefreshTokenRepository(db),
        pending_user_repo=SQLPendingUserRepository(db),
    )


                                                                    
@router.post(
    "/register",
    response_model=RegistrationPendingResponse,
    status_code=202,
    summary="Start organization registration and send an email verification link",
)
async def register(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    body: RegisterRequest,
    db: DBSession,
) -> RegistrationPendingResponse:
    service = _build_auth_service(db)
    result = await service.register_org(
        RegisterOrgCommand(
            org_name=body.org_name,
            org_slug=body.org_slug,
            user_name=body.name,
            email=body.email,
            password=body.password,
            ip_address=request.client.host if request.client else None,
        )
    )
    verification_url = (
        f"{settings.API_PUBLIC_URL.rstrip('/')}/api/v1/identity/auth/verify-email?"
        f"{urlencode({'token': result.raw_verification_token})}"
    )
    background_tasks.add_task(
        EmailAdapter().send_verification_email,
        recipient_email=result.pending_user.email,
        recipient_name=result.pending_user.name,
        verification_url=verification_url,
    )
    return RegistrationPendingResponse(
        message="Check your email to verify your account.", email=result.pending_user.email
    )


                                                                    
@router.get("/verify-email", response_class=HTMLResponse, summary="Verify a pending registration or workspace invitation")
async def verify_email(token: str, db: DBSession) -> HTMLResponse:
    result = await _build_auth_service(db).verify_email(token)
    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    if result.status == "already_verified":
        title = "Email already verified"
        message = (
            "Your workspace access is already verified and active."
            f"<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600'>Sign in to DecisionFlow AI</a>"
        )
    elif result.status == "expired":
        title = "Verification link expired"
        message = (
            "This verification link has expired or has already been used. Please ask your workspace administrator to resend an invitation."
            f"<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;border:1px solid #d0d5dd;color:#344054;text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:600'>Go to Sign in</a>"
        )
    elif result.status == "invitation_verified":
        reset_url = (
            f"{settings.API_PUBLIC_URL.rstrip('/')}/api/v1/identity/auth/forgot-password?"
            f"{urlencode({'token': result.raw_password_reset_token})}"
        )
        title = "Email verified successfully"
        message = (
            "Your workspace access is now activated and ready."
            f"<br/><br/><a href='{reset_url}' style='display:inline-block;margin-top:12px;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600'>Set your own password</a>"
            f"<br/><br/><span style='font-size:13px;color:#667085'>Or <a href='{login_url}' style='color:#2563eb'>sign in directly</a> with your temporary password.</span>"
        )
    else:
        title = "Email verified"
        message = (
            "Your organization is ready. You can now sign in to your workspace."
            f"<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600'>Sign in to DecisionFlow AI</a>"
        )
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>DecisionFlow AI — Verification</title></head><body style='margin:0;background:#090d16;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:#f0f6fc'><main style='max-width:540px;margin:80px auto;background:#111827;border:1px solid rgba(255,255,255,0.1);padding:48px 36px;border-radius:20px;text-align:center;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5)'><div style='font-size:24px;letter-spacing:0.15em;font-weight:800;color:#38bdf8'>DECISIONFLOW <span style='color:#a5f3fc'>AI</span></div><h1 style='margin-top:32px;font-size:26px;font-weight:700'>{title}</h1><div style='margin-top:16px;line-height:1.7;color:#94a3b8'>{message}</div></main></body></html>""")


@router.post(
    "/forgot-password",
    response_model=PasswordResetRequestResponse,
    status_code=202,
    summary="Request a password reset email",
)
async def forgot_password_request(
    request: Request,
    background_tasks: BackgroundTasks,
    body: ForgotPasswordRequest,
    db: DBSession,
) -> PasswordResetRequestResponse:
    service = _build_auth_service(db)
    result = await service.request_password_reset(
        RequestPasswordResetCommand(email=body.email)
    )
    if result.user:
        reset_url = (
            f"{settings.API_PUBLIC_URL.rstrip('/')}/api/v1/identity/auth/forgot-password?"
            f"{urlencode({'token': result.raw_token})}"
        )
        background_tasks.add_task(
            EmailAdapter().send_password_reset_email,
            recipient_email=result.user.email,
            recipient_name=result.user.name,
            reset_url=reset_url,
        )
    await db.commit()
    return PasswordResetRequestResponse(
        message="If an account exists for that email, a reset link has been sent."
    )


@router.get("/forgot-password", response_class=HTMLResponse, summary="Show the password reset form for a valid email token")
async def forgot_password_page(token: str, db: DBSession) -> HTMLResponse:
    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    service = _build_auth_service(db)
    status = await service.validate_password_reset_token(token)
    if status != "valid":
        return HTMLResponse(
            f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>DecisionFlow AI — Password Reset</title></head><body style='margin:0;background:#090d16;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:#f0f6fc'><main style='max-width:540px;margin:80px auto;background:#111827;border:1px solid rgba(255,255,255,0.1);padding:48px 36px;border-radius:20px;text-align:center;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5)'><div style='font-size:24px;letter-spacing:0.15em;font-weight:800;color:#38bdf8'>DECISIONFLOW <span style='color:#a5f3fc'>AI</span></div><h1 style='margin-top:32px;font-size:26px;font-weight:700'>Reset link expired</h1><div style='margin-top:16px;line-height:1.7;color:#94a3b8'>This password reset link is invalid or has expired. Please request a fresh one from the login page.<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;border:1px solid rgba(255,255,255,0.2);color:#f0f6fc;text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:600'>Go to Sign in</a></div></main></body></html>"""
        )
    hidden_token_field = f"<input type=\"hidden\" name=\"token\" value=\"{token}\" />"
    return HTMLResponse(
        f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>DecisionFlow AI — Set New Password</title></head><body style='margin:0;background:#090d16;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:#f0f6fc'><main style='max-width:540px;margin:80px auto;background:#111827;border:1px solid rgba(255,255,255,0.1);padding:48px 36px;border-radius:20px;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5)'><div style='text-align:center;font-size:24px;letter-spacing:0.15em;font-weight:800;color:#38bdf8'>DECISIONFLOW <span style='color:#a5f3fc'>AI</span></div><h1 style='margin-top:32px;font-size:26px;font-weight:700;text-align:center'>Set a new password</h1><p style='margin-top:8px;text-align:center;color:#94a3b8;font-size:14px'>Choose a strong password for your account.</p><form method='POST' action='/api/v1/identity/auth/forgot-password/confirm'>{hidden_token_field}<label style='display:block;margin:24px 0 8px;font-size:13px;color:#94a3b8;font-weight:500'>New password</label><input type='password' name='new_password' required minlength='8' placeholder='At least 8 characters' style='width:100%;padding:12px 16px;border:1px solid rgba(255,255,255,0.15);border-radius:12px;background:rgba(255,255,255,0.05);color:#f0f6fc;font-size:14px;outline:none;box-sizing:border-box' /><button type='submit' style='margin-top:24px;width:100%;background:#2563eb;color:#fff;border:0;padding:14px 18px;border-radius:12px;cursor:pointer;font-size:14px;font-weight:600'>Reset password</button></form></main></body></html>"""
    )


@router.post("/forgot-password/confirm", response_class=HTMLResponse, summary="Apply a new password for a valid reset token")
async def forgot_password_confirm(
    token: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    db: DBSession,
) -> HTMLResponse:
    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    service = _build_auth_service(db)
    result = await service.reset_password(
        ResetPasswordCommand(raw_token=token, new_password=new_password)
    )
    if result.status == "reset":
        title = "Password reset complete"
        message = (
            "Your password has been updated successfully. You can now sign in with your new password."
            f"<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600'>Sign in to DecisionFlow AI</a>"
        )
    else:
        title = "Reset link expired"
        message = (
            "This password reset link is invalid or has already been used. Please request a new one from the login page."
            f"<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;border:1px solid rgba(255,255,255,0.2);color:#f0f6fc;text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:600'>Go to Sign in</a>"
        )
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>DecisionFlow AI — Password Reset</title></head><body style='margin:0;background:#090d16;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:#f0f6fc'><main style='max-width:540px;margin:80px auto;background:#111827;border:1px solid rgba(255,255,255,0.1);padding:48px 36px;border-radius:20px;text-align:center;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5)'><div style='font-size:24px;letter-spacing:0.15em;font-weight:800;color:#38bdf8'>DECISIONFLOW <span style='color:#a5f3fc'>AI</span></div><h1 style='margin-top:32px;font-size:26px;font-weight:700'>{title}</h1><div style='margin-top:16px;line-height:1.7;color:#94a3b8'>{message}</div></main></body></html>""")


@router.get("/forgot-password/success", response_class=HTMLResponse, summary="Show a success page after a password reset")
async def forgot_password_success() -> HTMLResponse:
    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    return HTMLResponse(
        f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>DecisionFlow AI — Password Reset</title></head><body style='margin:0;background:#090d16;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:#f0f6fc'><main style='max-width:540px;margin:80px auto;background:#111827;border:1px solid rgba(255,255,255,0.1);padding:48px 36px;border-radius:20px;text-align:center;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5)'><div style='font-size:24px;letter-spacing:0.15em;font-weight:800;color:#38bdf8'>DECISIONFLOW <span style='color:#a5f3fc'>AI</span></div><h1 style='margin-top:32px;font-size:26px;font-weight:700'>Password reset complete</h1><div style='margin-top:16px;line-height:1.7;color:#94a3b8'>Your password has been updated successfully. You can now sign in with your new password.<br/><br/><a href='{login_url}' style='display:inline-block;margin-top:12px;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600'>Sign in to DecisionFlow AI</a></div></main></body></html>"""
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: DBSession,
) -> AuthResponse:
    service = _build_auth_service(db)
    result = await service.login(
        LoginCommand(
            email=body.email,
            password=body.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
    )
    _set_refresh_cookie(response, result.raw_refresh_token)
    return AuthResponse(
        user=map_user_to_response(result.user),
        organization=map_org_to_response(result.organization),
        tokens=make_token_response(result.access_token),
    )


                                                                    
@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Rotate refresh token and get new access token",
)
async def refresh_tokens(
    request: Request,
    response: Response,
    body: RefreshRequest,
    db: DBSession,
    df_refresh: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> RefreshResponse:
                                                         
    raw_token = body.refresh_token or df_refresh
    if not raw_token:
        raise InvalidTokenError("Refresh token required (cookie or body)")

    service = _build_auth_service(db)
    result = await service.refresh_tokens(
        RefreshTokensCommand(
            raw_refresh_token=raw_token,
            ip_address=request.client.host if request.client else None,
        )
    )
    _set_refresh_cookie(response, result.raw_refresh_token)
    return RefreshResponse(tokens=make_token_response(result.access_token))


                                                                    
@router.post(
    "/logout",
    status_code=204,
    summary="Revoke current session (or all sessions)",
)
async def logout(
    response: Response,
    body: LogoutRequest,
    db: DBSession,
    current_user: CurrentUser,
    df_refresh: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> None:
    raw_token = body.refresh_token or df_refresh
    service = _build_auth_service(db)
    await service.logout(
        LogoutCommand(
            user_id=current_user.id,
            raw_refresh_token=raw_token,
            logout_all=body.logout_all,
        )
    )
    _clear_refresh_cookie(response)


                                                                    
@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user and organization",
)
async def get_me(
    current_user: CurrentUser,
    db: DBSession,
) -> MeResponse:
    service = _build_user_service(db)
    user, org = await service.get_me(
        GetMeQuery(user_id=current_user.id, org_id=current_user.org_id)
    )
    return MeResponse(
        user=map_user_to_response(user),
        organization=map_org_to_response(org),
    )
