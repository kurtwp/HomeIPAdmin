"""adopt_lease service tests — importing live DHCP leases into the IP DB."""

from app.models.network import Network
from app.models.ip_address import IPAddress
from app.services.ip_service import adopt_lease


def _seed_network(db_session):
    net = Network(name="Office", cidr="192.168.50.0/24", vlan_id=50)
    db_session.add(net)
    db_session.commit()
    return net


def test_adopt_creates_new_record(db_session):
    net = _seed_network(db_session)
    created, msg = adopt_lease(
        db_session,
        {"ip": "192.168.50.10", "mac": "AA:BB:CC:DD:EE:01", "hostname": "printer", "is_static": False},
    )
    assert created is True
    ip = db_session.query(IPAddress).filter_by(address="192.168.50.10").one()
    assert ip.source == "unifi_client"
    assert ip.network_id == net.id
    assert ip.assignment_type.value == "dhcp"
    assert ip.status.value == "active"
    assert ip.hostname == "printer"
    assert ip.mac_address == "AA:BB:CC:DD:EE:01"


def test_adopt_static_lease(db_session):
    _seed_network(db_session)
    created, _ = adopt_lease(db_session, {"ip": "192.168.50.5", "is_static": True})
    assert created is True
    ip = db_session.query(IPAddress).filter_by(address="192.168.50.5").one()
    assert ip.assignment_type.value == "static"


def test_adopt_cleans_placeholder_hostname(db_session):
    _seed_network(db_session)
    adopt_lease(db_session, {"ip": "192.168.50.20", "hostname": "—", "is_static": False})
    ip = db_session.query(IPAddress).filter_by(address="192.168.50.20").one()
    assert ip.hostname is None


def test_adopt_updates_existing(db_session):
    _seed_network(db_session)
    adopt_lease(db_session, {"ip": "192.168.50.10", "hostname": "old", "is_static": False})
    created, msg = adopt_lease(
        db_session, {"ip": "192.168.50.10", "hostname": "new", "is_static": False}
    )
    assert created is False
    ips = db_session.query(IPAddress).filter_by(address="192.168.50.10").all()
    assert len(ips) == 1  # no duplicate
    assert ips[0].hostname == "new"
    assert ips[0].status.value == "active"


def test_adopt_no_matching_network(db_session):
    created, msg = adopt_lease(db_session, {"ip": "10.99.99.99", "is_static": False})
    assert created is False
    assert "network" in msg.lower()
    assert db_session.query(IPAddress).count() == 0


def test_adopt_no_ip(db_session):
    created, msg = adopt_lease(db_session, {})
    assert created is False


def test_adopt_invalid_ip(db_session):
    _seed_network(db_session)
    created, msg = adopt_lease(db_session, {"ip": "not-an-ip", "is_static": False})
    assert created is False
    assert "invalid" in msg.lower()
