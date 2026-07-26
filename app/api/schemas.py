"""Pydantic schemas for REST API request and response bodies."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(v: datetime | None) -> str | None:
    """Format a datetime as ISO-8601, or return None."""
    return v.isoformat() if v else None


# ---------------------------------------------------------------------------
# Summary schemas (used as nested refs in larger responses)
# ---------------------------------------------------------------------------

class TagSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    color: str


class IPAddressSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    address: str
    hostname: str | None = None


class DeviceTypeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    icon: str | None = None


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

class NetworkBase(BaseModel):
    name: str
    cidr: str
    vlan_id: int | None = None
    gateway: str | None = None
    dns_servers: str | None = None
    description: str | None = None
    notes: str | None = None
    is_favorite: bool = False
    parent_id: int | None = None
    dhcp_start: str | None = None
    dhcp_end: str | None = None


class NetworkCreate(NetworkBase):
    pass


class NetworkUpdate(BaseModel):
    name: str | None = None
    cidr: str | None = None
    vlan_id: int | None = None
    gateway: str | None = None
    dns_servers: str | None = None
    description: str | None = None
    notes: str | None = None
    is_favorite: bool | None = None
    parent_id: int | None = None
    dhcp_start: str | None = None
    dhcp_end: str | None = None


class NetworkResponse(NetworkBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str | None = None
    updated_at: str | None = None
    ip_count: int = 0

    @classmethod
    def from_model(cls, n: Any) -> NetworkResponse:
        return cls(
            id=n.id,
            name=n.name,
            cidr=n.cidr,
            vlan_id=n.vlan_id,
            gateway=n.gateway,
            dns_servers=n.dns_servers,
            description=n.description,
            notes=n.notes,
            is_favorite=n.is_favorite,
            parent_id=n.parent_id,
            dhcp_start=n.dhcp_start,
            dhcp_end=n.dhcp_end,
            created_at=_dt(n.created_at),
            updated_at=_dt(n.updated_at),
            ip_count=len(n.ip_addresses) if hasattr(n, "ip_addresses") else 0,
        )


# ---------------------------------------------------------------------------
# IP Address
# ---------------------------------------------------------------------------

class IPAddressBase(BaseModel):
    address: str
    hostname: str | None = None
    mac_address: str | None = None
    assignment_type: str = "dhcp"
    status: str = "unknown"
    notes: str | None = None
    source: str | None = None
    network_id: int
    device_id: int | None = None


class IPAddressCreate(IPAddressBase):
    pass


class IPAddressUpdate(BaseModel):
    address: str | None = None
    hostname: str | None = None
    mac_address: str | None = None
    assignment_type: str | None = None
    status: str | None = None
    notes: str | None = None
    source: str | None = None
    network_id: int | None = None
    device_id: int | None = None


class IPAddressResponse(IPAddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_seen: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[TagSummary] = []

    @classmethod
    def from_model(cls, ip: Any) -> IPAddressResponse:
        return cls(
            id=ip.id,
            address=ip.address,
            hostname=ip.hostname,
            mac_address=ip.mac_address,
            assignment_type=(
                ip.assignment_type.value
                if hasattr(ip.assignment_type, "value")
                else ip.assignment_type
            ),
            status=ip.status.value if hasattr(ip.status, "value") else ip.status,
            notes=ip.notes,
            source=ip.source,
            network_id=ip.network_id,
            device_id=ip.device_id,
            last_seen=_dt(ip.last_seen),
            created_at=_dt(ip.created_at),
            updated_at=_dt(ip.updated_at),
            tags=[TagSummary.model_validate(t) for t in ip.tags] if ip.tags else [],
        )


# ---------------------------------------------------------------------------
# Device Type
# ---------------------------------------------------------------------------

class DeviceTypeBase(BaseModel):
    name: str
    icon: str | None = None
    description: str | None = None


class DeviceTypeCreate(DeviceTypeBase):
    pass


class DeviceTypeResponse(DeviceTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    @classmethod
    def from_model(cls, dt: Any) -> DeviceTypeResponse:
        return cls(id=dt.id, name=dt.name, icon=dt.icon, description=dt.description)


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------

class DeviceBase(BaseModel):
    name: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    mac_address: str | None = None
    notes: str | None = None
    location: str | None = None
    rack_position: str | None = None
    shelf: str | None = None
    device_type_id: int | None = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    mac_address: str | None = None
    notes: str | None = None
    location: str | None = None
    rack_position: str | None = None
    shelf: str | None = None
    device_type_id: int | None = None


class DeviceResponse(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_date: str | None = None
    warranty_expiry: str | None = None
    eol_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    device_type: DeviceTypeSummary | None = None
    ip_addresses: list[IPAddressSummary] = []
    tags: list[TagSummary] = []

    @classmethod
    def from_model(cls, d: Any) -> DeviceResponse:
        return cls(
            id=d.id,
            name=d.name,
            manufacturer=d.manufacturer,
            model=d.model,
            serial_number=d.serial_number,
            mac_address=d.mac_address,
            notes=d.notes,
            location=d.location,
            rack_position=d.rack_position,
            shelf=d.shelf,
            device_type_id=d.device_type_id,
            purchase_date=_dt(d.purchase_date),
            warranty_expiry=_dt(d.warranty_expiry),
            eol_date=_dt(d.eol_date),
            created_at=_dt(d.created_at),
            updated_at=_dt(d.updated_at),
            device_type=DeviceTypeSummary(
                id=d.device_type.id, name=d.device_type.name, icon=d.device_type.icon
            ) if d.device_type else None,
            ip_addresses=[
                IPAddressSummary(id=ip.id, address=ip.address, hostname=ip.hostname)
                for ip in d.ip_addresses
            ] if d.ip_addresses else [],
            tags=[TagSummary.model_validate(t) for t in d.tags] if d.tags else [],
        )


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------

class TagBase(BaseModel):
    name: str
    color: str = "#1976d2"


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    @classmethod
    def from_model(cls, t: Any) -> TagResponse:
        return cls(id=t.id, name=t.name, color=t.color)


# ---------------------------------------------------------------------------
# Monitored Host (Uptime)
# ---------------------------------------------------------------------------

class MonitorBase(BaseModel):
    ip_address: str
    name: str
    monitor_type: str = "ping"
    port: int | None = None
    check_interval: int = 60
    max_retries: int = 3
    retry_interval: int = 30
    is_enabled: bool = True


class MonitorCreate(MonitorBase):
    pass


class MonitorUpdate(BaseModel):
    ip_address: str | None = None
    name: str | None = None
    monitor_type: str | None = None
    port: int | None = None
    check_interval: int | None = None
    max_retries: int | None = None
    retry_interval: int | None = None
    is_enabled: bool | None = None


class MonitorResponse(MonitorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_status: str = "unknown"
    last_check: str | None = None
    last_seen_up: str | None = None
    last_seen_down: str | None = None
    consecutive_failures: int = 0
    total_checks: int = 0
    total_up: int = 0
    uptime_percent: float = 0.0
    created_at: str | None = None

    @classmethod
    def from_model(cls, m: Any) -> MonitorResponse:
        return cls(
            id=m.id,
            ip_address=m.ip_address,
            name=m.name,
            monitor_type=m.monitor_type,
            port=m.port,
            check_interval=m.check_interval,
            max_retries=m.max_retries,
            retry_interval=m.retry_interval,
            is_enabled=m.is_enabled,
            current_status=m.current_status,
            last_check=_dt(m.last_check),
            last_seen_up=_dt(m.last_seen_up),
            last_seen_down=_dt(m.last_seen_down),
            consecutive_failures=m.consecutive_failures,
            total_checks=m.total_checks,
            total_up=m.total_up,
            uptime_percent=m.uptime_percent,
            created_at=_dt(m.created_at),
        )


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

class DocBase(BaseModel):
    title: str
    body: str = ""
    category: str = "general"
    linked_ip_id: int | None = None
    linked_device_id: int | None = None
    linked_network_id: int | None = None


class DocCreate(DocBase):
    pass


class DocUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    category: str | None = None
    linked_ip_id: int | None = None
    linked_device_id: int | None = None
    linked_network_id: int | None = None


class DocResponse(DocBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_model(cls, d: Any) -> DocResponse:
        return cls(
            id=d.id,
            title=d.title,
            body=d.body,
            category=d.category.value if hasattr(d.category, "value") else d.category,
            linked_ip_id=d.linked_ip_id,
            linked_device_id=d.linked_device_id,
            linked_network_id=d.linked_network_id,
            created_at=_dt(d.created_at),
            updated_at=_dt(d.updated_at),
        )


# ---------------------------------------------------------------------------
# Dashboard / Search
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    total_networks: int = 0
    total_ips: int = 0
    total_devices: int = 0
    active_ips: int = 0
    inactive_ips: int = 0
    unknown_ips: int = 0
    monitors_up: int = 0
    monitors_down: int = 0
    monitors_total: int = 0
    recent_changes: list[dict[str, Any]] = []


class SearchResult(BaseModel):
    networks: list[NetworkResponse] = []
    ip_addresses: list[IPAddressResponse] = []
    devices: list[DeviceResponse] = []
    docs: list[DocResponse] = []
