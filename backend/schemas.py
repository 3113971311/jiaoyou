from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ---- Auth ----
class LoginRequest(BaseModel): account: str; password: str
class RegisterRequest(BaseModel): username: str; email: str; password: str; code: str
class SendCodeRequest(BaseModel): email: str; purpose: str
class ResetPwdRequest(BaseModel): email: str; code: str; new_password: str
class ChangePwdRequest(BaseModel): old_password: str; new_password: str
class TokenResponse(BaseModel): access_token: str; refresh_token: str
class RefreshRequest(BaseModel): refresh_token: str

# ---- User ----
class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None; gender: Optional[str] = None
    birthday: Optional[str] = None; bio: Optional[str] = None
    location: Optional[str] = None

# ---- Moments ----
class CreateMomentRequest(BaseModel): content_text: Optional[str] = ""

# ---- Match ----
class StartMatchRequest(BaseModel):
    scope: str; latitude: float; longitude: float; prefer_gender: Optional[str] = None

# ---- Payment ----
class RedeemCardRequest(BaseModel): code: str
class BuyCardRequest(BaseModel): days: int; email: str
class SubmitOrderNoRequest(BaseModel): order_no: str
class BatchBillStatusRequest(BaseModel):
    ids: list[str]
    status: str
class VipPlanRequest(BaseModel):
    days: int
    price: float
    title: Optional[str] = ""
    description: Optional[str] = ""
    badge: Optional[str] = ""
    payment_qr_url: Optional[str] = ""
    first_discount_rate: float = 0
    first_discount_qr_url: Optional[str] = ""
    sort_order: int = 0
    is_active: bool = True

# ---- Card ----
class GenerateCardRequest(BaseModel):
    batch_name: str; denomination_days: int; expire_days: int = 7
    quantity: int; note: Optional[str] = None

# ---- Report ----
class SubmitReportRequest(BaseModel): target_type: str; target_id: str; reason: str
class HandleReportRequest(BaseModel): action: str; result: str = ""

# ---- Warning ----
class WarnUserRequest(BaseModel): reason: str; related_chat_image_url: Optional[str] = None

# ---- Batch Review ----
class BatchReviewRequest(BaseModel): ids: list[str]; action: str
class BatchDeleteRequest(BaseModel): ids: list[str]

# ---- Site Config ----
class UpdateConfigRequest(BaseModel): value: str; type: Optional[str] = None; description: Optional[str] = None

# ---- Feedback ----
class FeedbackRequest(BaseModel): title: str; content: str; contact: str = ""

# ---- User Admin ----
class CreateUserRequest(BaseModel):
    username: str; email: str; password: str; nickname: Optional[str] = None
    gender: Optional[str] = None; is_admin: bool = False; vip_days: int = 0

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None; email: Optional[str] = None
    password: Optional[str] = None; nickname: Optional[str] = None
    gender: Optional[str] = None; is_admin: Optional[bool] = None
    status: Optional[str] = None; vip_expires_at: Optional[str] = None
    vip_days: Optional[int] = None
