"""Configuration and environment variable loader for Aladin OpenAPI."""

import os
import sys

# SSL Truststore for Windows / Corporate / School network SSL interception
if sys.version_info >= (3, 10):
    try:
        import truststore
        truststore.inject_into_ssl()
    except Exception:
        pass


def get_ttb_key() -> str:
    """Retrieve Aladin TTB Key from environment or Windows registry."""
    key = os.environ.get("ALADIN_TTB_KEY") or os.environ.get("ALADIN_API_KEY") or os.environ.get("TTB_KEY")
    if key:
        return key.strip()

    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                val, _ = winreg.QueryValueEx(k, "ALADIN_TTB_KEY")
                if val:
                    return str(val).strip()
        except Exception:
            pass

    return ""


API_BASE_URL = "https://www.aladin.co.kr/ttb/api"
API_SEARCH_URL = f"{API_BASE_URL}/ItemSearch.aspx"
API_LOOKUP_URL = f"{API_BASE_URL}/ItemLookUp.aspx"
API_LIST_URL = f"{API_BASE_URL}/ItemList.aspx"
API_VERSION = "20131101"
