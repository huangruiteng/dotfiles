"""Legacy personal profile adapter; LoopX owns account IO and recovery.

Install the optional loopx-codex-provider-routing package. No copied account
writer or credential fallback lives in dotfiles.
"""
from pathlib import Path

try:
    from loopx_codex_provider_routing import native_account_store as _owner
except ImportError:
    raise ValueError("Install or upgrade loopx-codex-provider-routing for native account commands") from None

API_KEY_SLOTS_VERSION = _owner.API_KEY_SLOTS_VERSION
api_endpoint = _owner.api_endpoint
auth_kind = _owner.auth_kind
checked = _owner.checked
digest = _owner.digest
private_dir = _owner.private_dir
atomic = _owner.atomic
encoded = _owner.encoded
read_private = _owner.read_private
identity = _owner.identity
file_config = _owner.file_config


def profile(home, spec):
    lock_root = Path(home) / ".local/state/personal-apps"
    return {**spec, "lock_root": lock_root, "account_store": lock_root / "gpt-accounts"}


def credential_lock(home, shared=False):
    return _owner.credential_lock(home, shared=shared, lock_root=profile(home, {})["lock_root"])


class Accounts(_owner.Accounts):
    def __init__(self, home, spec, idle, login_cli, env):
        super().__init__(home, profile(home, spec), idle, login_cli, env)
