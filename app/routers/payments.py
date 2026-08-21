from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.models import Venue, Package, Payment, PaymentStatus, WifiSession, User
from app.schemas.schemas import STKPushRequest, STKPushResponse, PaymentOut
from app.services.mpesa import MpesaService
from app.core.deps import get_current_user
from app.radius_database import RadiusSessionLocal
from app.services.radius import create_radius_user, generate_password

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/stk-push", response_model=STKPushResponse, status_code=status.HTTP_201_CREATED)
async def initiate_stk_push(payload: STKPushRequest, db: Session = Depends(get_db)):
    # Public endpoint - called from the captive portal
    venue = db.query(Venue).filter(Venue.id == payload.venue_id, Venue.is_active == True).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found or inactive")

    package = db.query(Package).filter(
        Package.id == payload.package_id,
        Package.venue_id == payload.venue_id,
        Package.is_active == True
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found or inactive")

    payment = Payment(
        venue_id=venue.id,
        package_id=package.id,
        phone_number=payload.phone_number,
        amount=package.price,
        status=PaymentStatus.PENDING,
        mac_address=payload.mac_address,
        ip_address=payload.ip_address,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)


    owner = venue.owner


    mpesa = MpesaService(
        consumer_key=owner.mpesa_consumer_key, 
        consumer_secret=owner.mpesa_consumer_secret,
        shortcode=owner.mpesa_shortcode,
        passkey=owner.mpesa_passkey, 
    )

    try:
        amount = int(package.price)
        result = await mpesa.stk_push(
            phone_number=payload.phone_number,
            amount=amount,
            account_reference=f"WIFI{payment.id}",
            transaction_desc=package.name[:13],
        )

        payment.checkout_request_id = result.get("CheckoutRequestID")
        payment.merchant_request_id = result.get("MerchantRequestID")
        db.commit()
        db.refresh(payment)

        return STKPushResponse(
            message="STK Push initiated successfully",
            payment_id=payment.id,
            checkout_request_id=result.get("CheckoutRequestID"),
            merchant_request_id=result.get("MerchantRequestID"),
            customer_message=result.get("CustomerMessage"),
        )
    except Exception as e:
        payment.status = PaymentStatus.FAILED
        payment.result_desc = str(e)
        db.commit()
        raise HTTPException(status_code=502, detail=f"Failed to initiate STK Push: {str(e)}")


@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    print("\n========== MPESA CALLBACK RECEIVED ==========")
    print(body)
    print("=============================================\n")

    try:
        stk_callback = body.get("Body", {}).get("stkCallback", {})
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")

        if not checkout_request_id:
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        payment = db.query(Payment).filter(Payment.checkout_request_id == checkout_request_id).first()
        if not payment:
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        if payment.status != PaymentStatus.PENDING:
            return {"ResultCode": 0, "ResultDesc": "Accepted"}

        payment.result_code = str(result_code)
        payment.result_desc = result_desc

        if result_code == 0:
            payment.status = PaymentStatus.SUCCESS

            metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
            for item in metadata:
                if item.get("Name") == "MpesaReceiptNumber":
                    payment.mpesa_receipt_number = str(item.get("Value"))
                    break

            package = payment.package
            starts_at = datetime.now(timezone.utc)
            expires_at = starts_at + timedelta(minutes=package.duration_minutes)

            session = WifiSession(
                venue_id=payment.venue_id,
                payment_id=payment.id,
                mac_address=payment.mac_address or "unknown",
                ip_address=payment.ip_address,
                username=f"user_{payment.id}",
                starts_at=starts_at,
                expires_at=expires_at,
                is_active=True,
            )
            db.add(session)

            # Create RADIUS user
            radius_db = RadiusSessionLocal()
            try:
                username = payment.phone_number.replace(" ", "").replace("+", "")
                if username.startswith("0"):
                    username = "254" + username[1:]

                password = generate_password(8)
                session_timeout = package.duration_minutes * 60
                max_devices = package.max_devices or 1

                create_radius_user(
                    db=radius_db,
                    username=username,
                    password=password,
                    session_timeout=session_timeout,
                    max_devices=max_devices
                )
                session.username = username
                print(f"RADIUS user created → {username} / {password}")
            except Exception as e:
                print(f"Failed to create RADIUS user: {e}")
            finally:
                radius_db.close()

        else:
            payment.status = PaymentStatus.FAILED

        db.commit()
    except Exception as e:
        print(f"Callback error: {e}")
        db.rollback()

    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.get("/", response_model=List[PaymentOut])
def list_payments(
    venue_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment).join(Venue).filter(Venue.owner_id == current_user.id)
    if venue_id:
        query = query.filter(Payment.venue_id == venue_id)
    return query.order_by(Payment.created_at.desc()).limit(100).all()


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).join(Venue).filter(
        Payment.id == payment_id,
        Venue.owner_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/{payment_id}/status")
def get_payment_status(payment_id: int, db: Session = Depends(get_db)):
    """
    Public endpoint used by the captive portal to check payment status.
    Returns only safe, limited fields.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "id": payment.id,
        "status": payment.status,
        "mpesa_receipt_number": payment.mpesa_receipt_number,
    }