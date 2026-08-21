import base64
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import get_settings

settings = get_settings()


class MpesaService:
    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        shortcode: Optional[str] = None,
        passkey: Optional[str] = None,
    ):
        # Use venue credentials if provided, otherwise fall back to global sandbox
        self.consumer_key = consumer_key or settings.MPESA_CONSUMER_KEY
        self.consumer_secret = consumer_secret or settings.MPESA_CONSUMER_SECRET
        self.shortcode = shortcode or settings.MPESA_SHORTCODE
        self.passkey = passkey or settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.env = settings.MPESA_ENV

        if self.env == "sandbox":
            self.base_url = "https://sandbox.safaricom.co.ke"
        else:
            self.base_url = "https://api.safaricom.co.ke"

    async def get_access_token(self) -> str:
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        print("=== DEBUG: M-Pesa Credentials ===")
        print("Consumer Key length:", len(self.consumer_key) if self.consumer_key else 0)
        print("Consumer Key starts with:", self.consumer_key[:10] if self.consumer_key else "None")
        print("Consumer Secret length:", len(self.consumer_secret) if self.consumer_secret else 0)
        print("Shortcode:", self.shortcode)
        print("Base URL:", self.base_url)
        print("================================")
        auth = (self.consumer_key, self.consumer_secret)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth, timeout=30.0)
            if response.status_code != 200:
                print("=== MPESA TOKEN ERROR ===")
                print("Status:", response.status_code)
                print("Response body:", response.text)
                print("=========================")
                response.raise_for_status()
            #response.raise_for_status()
            print("=== RAW RESPONSE ===")
            print("Status:", response.status_code)
            print("Body:", response.text)
            print("====================")
            data = response.json()
            print("Token obtained succcessfully")
            return data["access_token"]

    def _generate_password(self) -> tuple[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(data_to_encode.encode()).decode("utf-8")
        return password, timestamp

    def _format_phone(self, phone: str) -> str:
        """Normalize phone to 2547XXXXXXXX format"""
        phone = phone.strip().replace(" ", "").replace("+", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("7"):
            phone = "254" + phone
        elif phone.startswith("1"):
            phone = "254" + phone
        return phone

    async def stk_push(
        self,
        phone_number: str,
        amount: int,
        account_reference: str = "HotspotPay",
        transaction_desc: str = "WiFi Package",
    ) -> Dict[str, Any]:
        """
        Initiate STK Push.
        amount should be an integer (KES).
        """
        access_token = await self.get_access_token()
        password, timestamp = self._generate_password()
        phone = self._format_phone(phone_number)

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference[:12],  # max 12 chars
            "TransactionDesc": transaction_desc[:13],
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        print("\n========== STK PUSH REQUEST ==========")
        print("URL:", url)
        print("Payload:", payload)
        print("======================================\n")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            print("\n========== STK PUSH RESPONSE ==========")
            print("Status Code:", response.status_code)
            print("Response Body:", response.text)
            print("==================================\n")
            response.raise_for_status()
            return response.json()