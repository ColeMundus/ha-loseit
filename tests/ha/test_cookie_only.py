"""Cookie-only distribution must not retain a hidden password login runtime."""

from pathlib import Path


def test_password_login_is_not_distributed():
    component = Path(__file__).resolve().parents[2] / "custom_components" / "loseit"
    assert not (component / "auth.py").exists()
    from custom_components.loseit.config_flow import LoseItConfigFlow

    assert not hasattr(LoseItConfigFlow, "async_step_password")
