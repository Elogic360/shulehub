import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings
from app.models.communication import MessageDeliveryStatus

logger = logging.getLogger(__name__)


class AfricasTalkingProviderError(Exception):
    pass


class AfricasTalkingClient:
    """
    Africa's Talking SMS API client supporting Sandbox and Production environments.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
        sender_id: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        self.username = username or settings.AFRICASTALKING_USERNAME
        self.api_key = api_key or settings.AFRICASTALKING_API_KEY
        self.sender_id = sender_id or settings.AFRICASTALKING_SENDER_ID
        self.environment = environment or settings.AFRICASTALKING_ENVIRONMENT

        if self.environment.lower() == "production":
            self.base_url = "https://api.africastalking.com/version1/messaging"
        else:
            self.base_url = "https://api.sandbox.africastalking.com/version1/messaging"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apiKey": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def send_sms(
        self,
        recipients: List[str],
        message: str,
        sender_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends SMS to one or more recipient phone numbers (E.164 format).
        Returns parsed Africa's Talking response dictionary.
        """
        if not recipients:
            raise AfricasTalkingProviderError("Recipients list cannot be empty")

        to_param = ",".join(recipients)
        payload = {
            "username": self.username,
            "to": to_param,
            "message": message,
        }

        active_sender = sender_id or self.sender_id
        # In sandbox, sender IDs must match sandbox shortcode or be omitted
        if active_sender and self.environment.lower() == "production":
            payload["from"] = active_sender

        headers = self._get_headers()

        # Mock / Sandbox safety check
        if self.api_key == "atsk_sandbox_placeholder" or self.environment == "test":
            logger.info("Using simulated Africa's Talking provider response for test/placeholder mode")
            mock_recipients = []
            for r in recipients:
                mock_recipients.append({
                    "statusCode": 101,
                    "number": r,
                    "status": "Success",
                    "cost": "TZS 25.0000",
                    "messageId": f"ATXid_mock_{hash(r + message) & 0xffffffff:08x}",
                })
            return {
                "SMSMessageData": {
                    "Message": f"Sent to {len(recipients)}/{len(recipients)} Total Cost: TZS {len(recipients)*25}.0000",
                    "Recipients": mock_recipients,
                }
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(self.base_url, data=payload, headers=headers)
                if response.status_code not in (200, 201):
                    logger.error(f"Africa's Talking API error {response.status_code}: {response.text}")
                    raise AfricasTalkingProviderError(f"HTTP {response.status_code}: {response.text}")

                data = response.json()
                return data
            except httpx.RequestError as exc:
                logger.error(f"Network error calling Africa's Talking API: {exc}")
                raise AfricasTalkingProviderError(f"Network error: {str(exc)}") from exc

    @staticmethod
    def map_provider_status_to_domain(status_str: str) -> MessageDeliveryStatus:
        """
        Maps raw Africa's Talking status strings to domain MessageDeliveryStatus.
        """
        normalized = (status_str or "").strip().lower()
        if normalized in ("success", "delivered"):
            return MessageDeliveryStatus.DELIVERED
        elif normalized in ("sent",):
            return MessageDeliveryStatus.SENT
        elif normalized in ("submitted", "buffered"):
            return MessageDeliveryStatus.SUBMITTED
        elif normalized in ("queued",):
            return MessageDeliveryStatus.QUEUED
        elif normalized in ("rejected", "riskhold", "usernotinblacklist"):
            return MessageDeliveryStatus.REJECTED
        elif normalized in ("failed", "couldnotroute", "invalidphonenumber"):
            return MessageDeliveryStatus.FAILED
        elif normalized in ("expired",):
            return MessageDeliveryStatus.EXPIRED
        elif normalized in ("cancelled",):
            return MessageDeliveryStatus.CANCELLED
        return MessageDeliveryStatus.UNKNOWN


default_at_client = AfricasTalkingClient()
