"""Notification service — sends alerts via email, webhook, Pushover, or Telegram.

Supports multiple channels with per-event toggle via NotificationPreference.
Configure channels via .env variables.
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

import httpx

from app.database.db import get_session
from app.models.notification_log import NotificationLog
from app.models.notification_preference import NotificationPreference

# All known event types for the preferences UI
EVENT_TYPES = [
    "host_down",
    "host_recovered",
    "firmware_update",
    "new_device",
    "capacity_warning",
    "scan_complete",
    "ssl_check_failed",
    "domain_check_failed",
]


# --- Configuration ---

def _get_config() -> dict:
    """Load notification config fresh from .env file (not cached os.environ)."""
    from dotenv import dotenv_values
    from pathlib import Path

    env_path = Path(__file__).parent.parent.parent / ".env"
    env = dotenv_values(env_path) if env_path.exists() else {}

    def _get(key: str, default: str = "") -> str:
        return env.get(key, os.getenv(key, default))

    return {
        "enabled": _get("NOTIFICATIONS_ENABLED", "false").lower() == "true",
        # Email (SMTP)
        "email_enabled": _get("NOTIFY_EMAIL_ENABLED", "false").lower() == "true",
        "smtp_host": _get("NOTIFY_SMTP_HOST", ""),
        "smtp_port": int(_get("NOTIFY_SMTP_PORT", "587")),
        "smtp_user": _get("NOTIFY_SMTP_USER", ""),
        "smtp_pass": _get("NOTIFY_SMTP_PASS", ""),
        "smtp_from": _get("NOTIFY_SMTP_FROM", ""),
        "smtp_to": _get("NOTIFY_SMTP_TO", ""),  # comma-separated
        "smtp_tls": _get("NOTIFY_SMTP_TLS", "true").lower() == "true",
        # Webhook (generic)
        "webhook_enabled": _get("NOTIFY_WEBHOOK_ENABLED", "false").lower() == "true",
        "webhook_url": _get("NOTIFY_WEBHOOK_URL", ""),
        # Pushover
        "pushover_enabled": _get("NOTIFY_PUSHOVER_ENABLED", "false").lower() == "true",
        "pushover_token": _get("NOTIFY_PUSHOVER_TOKEN", ""),
        "pushover_user": _get("NOTIFY_PUSHOVER_USER", ""),
        # Telegram
        "telegram_enabled": _get("NOTIFY_TELEGRAM_ENABLED", "false").lower() == "true",
        "telegram_bot_token": _get("NOTIFY_TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": _get("NOTIFY_TELEGRAM_CHAT_ID", ""),
    }


def is_notifications_enabled() -> bool:
    """Check if notifications are enabled globally."""
    return _get_config()["enabled"]


def get_enabled_channels() -> list[str]:
    """Return list of enabled notification channels."""
    config = _get_config()
    channels = []
    if config["email_enabled"]:
        channels.append("email")
    if config["webhook_enabled"]:
        channels.append("webhook")
    if config["pushover_enabled"]:
        channels.append("pushover")
    if config["telegram_enabled"]:
        channels.append("telegram")
    return channels


# --- Send Functions ---

def send_notification(
    subject: str,
    message: str,
    priority: str = "normal",
    event_type: str | None = None,
) -> list[dict]:
    """
    Send a notification through all enabled channels.

    Args:
        subject: Short summary/title
        message: Full message body
        priority: "low", "normal", "high", "critical"
        event_type: Event category (e.g. "host_down", "new_device"). If provided,
                    per-channel preferences from notification_preferences table are
                    checked before sending.

    Returns:
        List of results per channel: [{"channel": str, "success": bool, "error": str|None}]
    """
    config = _get_config()
    if not config["enabled"]:
        return []

    # Build set of channels to skip based on per-event preferences
    skipped_channels: set[str] = set()
    if event_type:
        skipped_channels = _get_disabled_channels(event_type)

    channels = [
        ("email", config["email_enabled"], lambda: _send_email(config, subject, message)),
        ("webhook", config["webhook_enabled"], lambda: _send_webhook(config, subject, message, priority)),
        ("pushover", config["pushover_enabled"], lambda: _send_pushover(config, subject, message, priority)),
        ("telegram", config["telegram_enabled"], lambda: _send_telegram(config, subject, message)),
    ]

    results: list[dict] = []
    for channel_name, channel_enabled, send_fn in channels:
        if not channel_enabled:
            continue
        if channel_name in skipped_channels:
            continue
        results.append(send_fn())

    # Log all notifications
    with get_session() as session:
        for result in results:
            log = NotificationLog(
                channel=result["channel"],
                subject=subject,
                message=message,
                success=result["success"],
                error=result.get("error"),
            )
            session.add(log)
        session.commit()

    return results


def _send_email(config: dict, subject: str, message: str) -> dict:
    """Send notification via SMTP email."""
    try:
        msg = MIMEMultipart()
        msg["From"] = config["smtp_from"]
        msg["To"] = config["smtp_to"]
        msg["Subject"] = f"[HomeLab] {subject}"

        body = MIMEText(message, "plain")
        msg.attach(body)

        if config["smtp_tls"]:
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])
            server.starttls()
        else:
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])

        if config["smtp_user"] and config["smtp_pass"]:
            server.login(config["smtp_user"], config["smtp_pass"])

        recipients = [r.strip() for r in config["smtp_to"].split(",")]
        server.sendmail(config["smtp_from"], recipients, msg.as_string())
        server.quit()

        return {"channel": "email", "success": True, "error": None}
    except Exception as e:
        return {"channel": "email", "success": False, "error": str(e)}


def _send_webhook(config: dict, subject: str, message: str, priority: str) -> dict:
    """Send notification via generic webhook (JSON POST). Auto-detects Discord/Slack format."""
    try:
        url = config["webhook_url"]

        # Discord webhooks need {"content": "text"} format
        if "discord.com/api/webhooks" in url:
            payload = {"content": f"**{subject}**\n{message}"}
        # Slack webhooks need {"text": "text"} format
        elif "hooks.slack.com" in url:
            payload = {"text": f"*{subject}*\n{message}"}
        else:
            # Generic JSON payload
            payload = {
                "subject": subject,
                "message": message,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "HomeLab Manager",
            }

        r = httpx.post(url, json=payload, timeout=10.0)
        r.raise_for_status()
        return {"channel": "webhook", "success": True, "error": None}
    except Exception as e:
        return {"channel": "webhook", "success": False, "error": str(e)}


def _send_pushover(config: dict, subject: str, message: str, priority: str) -> dict:
    """Send notification via Pushover API."""
    try:
        # Map priority to Pushover levels
        pushover_priority = {
            "low": -1,
            "normal": 0,
            "high": 1,
            "critical": 2,
        }.get(priority, 0)

        payload = {
            "token": config["pushover_token"],
            "user": config["pushover_user"],
            "title": subject,
            "message": message,
            "priority": pushover_priority,
        }

        # Critical priority requires retry/expire params
        if pushover_priority == 2:
            payload["retry"] = 60
            payload["expire"] = 3600

        r = httpx.post(
            "https://api.pushover.net/1/messages.json",
            data=payload,
            timeout=10.0,
        )
        r.raise_for_status()
        return {"channel": "pushover", "success": True, "error": None}
    except Exception as e:
        return {"channel": "pushover", "success": False, "error": str(e)}


def _send_telegram(config: dict, subject: str, message: str) -> dict:
    """Send notification via Telegram Bot API."""
    try:
        bot_token = config["telegram_bot_token"]
        chat_id = config["telegram_chat_id"]

        text = f"*{subject}*\n\n{message}"

        r = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10.0,
        )
        r.raise_for_status()
        return {"channel": "telegram", "success": True, "error": None}
    except Exception as e:
        return {"channel": "telegram", "success": False, "error": str(e)}


# --- Per-Event Preferences ---

def _get_disabled_channels(event_type: str) -> set[str]:
    """Return set of channel names disabled for a given event type."""
    with get_session() as session:
        prefs = (
            session.query(NotificationPreference)
            .filter(
                NotificationPreference.event_type == event_type,
                NotificationPreference.enabled == False,
            )
            .all()
        )
        return {p.channel for p in prefs}


def get_all_preferences() -> dict[str, dict[str, bool]]:
    """Return all notification preferences as {event_type: {channel: enabled}}.

    Only returns explicitly set preferences. Channels not in the DB default to True.
    """
    with get_session() as session:
        prefs = session.query(NotificationPreference).all()
    result: dict[str, dict[str, bool]] = {}
    for p in prefs:
        result.setdefault(p.event_type, {})[p.channel] = p.enabled
    return result


def set_preference(event_type: str, channel: str, enabled: bool) -> None:
    """Create or update a notification preference for a specific event/channel."""
    with get_session() as session:
        pref = (
            session.query(NotificationPreference)
            .filter(
                NotificationPreference.event_type == event_type,
                NotificationPreference.channel == channel,
            )
            .first()
        )
        if pref is None:
            pref = NotificationPreference(
                event_type=event_type, channel=channel, enabled=enabled
            )
            session.add(pref)
        else:
            pref.enabled = enabled
        session.commit()


def get_event_type_label(event_type: str) -> str:
    """Human-readable label for an event type."""
    labels = {
        "host_down": "Host Down",
        "host_recovered": "Host Recovered",
        "firmware_update": "Firmware Update Available",
        "new_device": "New Device Detected",
        "capacity_warning": "Capacity Warning",
        "scan_complete": "Scan Complete",
        "ssl_check_failed": "SSL Certificate Check Failed",
        "domain_check_failed": "Domain Check Failed",
    }
    return labels.get(event_type, event_type)


# --- Convenience Functions for Common Alerts ---

def notify_host_down(host_name: str, ip_address: str, consecutive_failures: int) -> list[dict]:
    """Send alert when an uptime-monitored host goes down."""
    subject = f"🔴 Host DOWN: {host_name} ({ip_address})"
    message = (
        f"Host '{host_name}' at {ip_address} is not responding.\n"
        f"Consecutive failures: {consecutive_failures}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="high", event_type="host_down")


def notify_host_recovered(host_name: str, ip_address: str, downtime_checks: int) -> list[dict]:
    """Send alert when a host recovers from being down."""
    subject = f"🟢 Host RECOVERED: {host_name} ({ip_address})"
    message = (
        f"Host '{host_name}' at {ip_address} is back online.\n"
        f"Was down for {downtime_checks} check(s).\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="normal", event_type="host_recovered")


def notify_firmware_update(device_name: str, current_version: str, available_version: str) -> list[dict]:
    """Send alert when a firmware update is available."""
    subject = f"📦 Firmware update: {device_name}"
    message = (
        f"Device '{device_name}' has a firmware update available.\n"
        f"Current: {current_version}\n"
        f"Available: {available_version}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="low", event_type="firmware_update")


def notify_new_device(device_name: str, ip_address: str, mac_address: str) -> list[dict]:
    """Send alert when a new device is detected on the network."""
    subject = f"🆕 New device: {device_name}"
    message = (
        f"A new device was detected on the network.\n"
        f"Name: {device_name}\n"
        f"IP: {ip_address}\n"
        f"MAC: {mac_address}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="normal", event_type="new_device")


def notify_capacity_warning(network_name: str, used: int, total: int) -> list[dict]:
    """Send alert when IP capacity exceeds threshold."""
    pct = round(used / total * 100, 1) if total > 0 else 0
    subject = f"⚠️ Capacity warning: {network_name}"
    message = (
        f"Network '{network_name}' is at {pct}% capacity.\n"
        f"Used: {used} / {total} addresses\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="normal", event_type="capacity_warning")


def notify_scan_complete(networks_scanned: int, new_devices: int) -> list[dict]:
    """Send notification when a scheduled scan finishes."""
    subject = f"🔍 Scan complete: {networks_scanned} network(s)"
    message = (
        f"Network scan completed.\n"
        f"Networks scanned: {networks_scanned}\n"
        f"New devices found: {new_devices}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="low", event_type="scan_complete")


def notify_ssl_check_failed(domain: str, error: str) -> list[dict]:
    """Send alert when an SSL certificate check fails."""
    subject = f"🔒 SSL check failed: {domain}"
    message = (
        f"SSL certificate check failed for '{domain}'.\n"
        f"Error: {error}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="high", event_type="ssl_check_failed")


def notify_domain_check_failed(domain: str, error: str) -> list[dict]:
    """Send alert when a domain WHOIS check fails."""
    subject = f"🌐 Domain check failed: {domain}"
    message = (
        f"Domain WHOIS check failed for '{domain}'.\n"
        f"Error: {error}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return send_notification(subject, message, priority="normal", event_type="domain_check_failed")


def get_notification_history(limit: int = 50) -> list[NotificationLog]:
    """Get recent notification log entries."""
    with get_session() as session:
        return (
            session.query(NotificationLog)
            .order_by(NotificationLog.timestamp.desc())
            .limit(limit)
            .all()
        )
