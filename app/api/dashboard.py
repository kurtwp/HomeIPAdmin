"""Dashboard statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.api.schemas import DashboardStats
from app.models.changelog import Changelog
from app.models.device import Device
from app.models.ip_address import IPAddress, IPStatus
from app.models.network import Network
from app.models.uptime_monitor import MonitoredHost

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    _key: str = Depends(verify_api_key),
):
    """Return aggregate statistics for the dashboard."""
    total_networks = db.query(Network).count()
    total_ips = db.query(IPAddress).count()
    total_devices = db.query(Device).count()

    active_ips = db.query(IPAddress).filter(IPAddress.status == IPStatus.ACTIVE).count()
    inactive_ips = (
        db.query(IPAddress).filter(IPAddress.status == IPStatus.INACTIVE).count()
    )
    unknown_ips = total_ips - active_ips - inactive_ips

    monitors_total = db.query(MonitoredHost).count()
    monitors_up = (
        db.query(MonitoredHost).filter(MonitoredHost.current_status == "up").count()
    )
    monitors_down = (
        db.query(MonitoredHost).filter(MonitoredHost.current_status == "down").count()
    )

    recent = (
        db.query(Changelog)
        .order_by(Changelog.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_changes = [
        {
            "id": c.id,
            "entity_type": c.entity_type.value if hasattr(c.entity_type, "value") else c.entity_type,
            "entity_name": c.entity_name,
            "action": c.action.value if hasattr(c.action, "value") else c.action,
            "timestamp": c.timestamp.isoformat() if c.timestamp else None,
        }
        for c in recent
    ]

    return DashboardStats(
        total_networks=total_networks,
        total_ips=total_ips,
        total_devices=total_devices,
        active_ips=active_ips,
        inactive_ips=inactive_ips,
        unknown_ips=unknown_ips,
        monitors_up=monitors_up,
        monitors_down=monitors_down,
        monitors_total=monitors_total,
        recent_changes=recent_changes,
    )
