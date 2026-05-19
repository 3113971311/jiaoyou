import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx


DEFAULT_MONITOR_DIR = r"D:\支付宝账单监测"
DEFAULT_SERVICE_PORT = 3031
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def monitor_dir() -> Path:
    return Path(os.getenv("ALIPAY_MONITOR_DIR", DEFAULT_MONITOR_DIR))


def service_script() -> Path:
    return monitor_dir() / "src" / "service.js"


def service_port() -> int:
    return int(os.getenv("ALIPAY_MONITOR_PORT", str(DEFAULT_SERVICE_PORT)))


def service_base_url() -> str:
    return f"http://127.0.0.1:{service_port()}"


def ensure_monitor_ready():
    root = monitor_dir()
    script = service_script()
    if not root.exists():
        raise RuntimeError(f"支付宝账单监测目录不存在: {root}")
    if not script.exists():
        raise RuntimeError(f"支付宝账单监测服务脚本不存在: {script}")
    return root, script


def base_env():
    root, _ = ensure_monitor_ready()
    env = os.environ.copy()
    env.setdefault("PLAYWRIGHT_PROFILE_DIR", str(root / "playwright-profile"))
    env.setdefault("DATA_DIR", str(root / "data"))
    env.setdefault("AUTO_EXPORT", "0")
    env.setdefault("SAVE_FILES", "0")
    env.setdefault("BILL_SCOPE", "all")
    env.setdefault("ALIPAY_MONITOR_PORT", str(service_port()))
    return env


def node_executable() -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("未找到 Node.js，请先安装或把 node 加入 PATH")
    return node


def stop_stale_profile_browsers():
    profile_path = str((monitor_dir() / "playwright-profile")).replace("'", "''")
    command = (
        f"$profilePath = '{profile_path}'; "
        "Get-CimInstance Win32_Process | "
        "Where-Object { ($_.Name -eq 'msedge.exe' -or $_.Name -eq 'chrome.exe') -and $_.CommandLine -like ('*' + $profilePath + '*') } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=20,
    )


def service_request(method: str, path: str, json_body=None, timeout_seconds: float = 10):
    url = f"{service_base_url()}{path}"
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.request(method, url, json=json_body)
    if response.status_code >= 400:
        try:
            payload = response.json()
            detail = payload.get("detail") or payload
        except Exception:
            detail = response.text
        raise RuntimeError(str(detail))
    return response.json()


def service_running() -> bool:
    try:
        payload = service_request("GET", "/status", timeout_seconds=5)
        return bool(payload.get("ok"))
    except Exception:
        return False


def ensure_service_running():
    if service_running():
        return

    stop_stale_profile_browsers()
    root, script = ensure_monitor_ready()
    subprocess.Popen(
        [node_executable(), str(script)],
        cwd=str(root),
        env=base_env(),
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 20
    while time.time() < deadline:
        if service_running():
            return
        time.sleep(0.5)
    raise RuntimeError("支付宝账单监测服务启动失败")


def monitor_status():
    ensure_service_running()
    return service_request("GET", "/status", timeout_seconds=5)


def launch_login_window(account: str = "", password: str = ""):
    ensure_service_running()
    payload = {}
    if account.strip():
        payload["account"] = account.strip()
    if password.strip():
        payload["password"] = password
    return service_request("POST", "/login", json_body=payload or None, timeout_seconds=60)


def sync_bills_once():
    ensure_service_running()
    return service_request("POST", "/sync", timeout_seconds=60)


def poll_match_order(order_no: str, amount: float, timeout_ms: int = 60_000, poll_interval_ms: int = 3_000):
    ensure_service_running()
    return service_request(
        "POST",
        "/match",
        json_body={
            "orderNo": order_no,
            "amount": amount,
            "timeoutMs": timeout_ms,
            "pollIntervalMs": poll_interval_ms,
        },
        timeout_seconds=max(90, int(timeout_ms / 1000) + 30),
    )
