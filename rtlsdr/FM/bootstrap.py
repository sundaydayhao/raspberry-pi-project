#!/usr/bin/env python3

from __future__ import annotations

import sys
import types


def _install_rtlsdr_fallback() -> None:
    try:
        import rtlsdr  # noqa: F401
        return
    except (ImportError, AttributeError) as exc:
        fallback_reason = str(exc)
        for module_name in list(sys.modules):
            if module_name == "rtlsdr" or module_name.startswith("rtlsdr."):
                sys.modules.pop(module_name, None)

        from compat_rtlsdr import RtlSdr

        shim = types.ModuleType("rtlsdr")
        shim.RtlSdr = RtlSdr
        sys.modules["rtlsdr"] = shim
        print(
            f"[WARN] Using local RTL-SDR wrapper because pyrtlsdr import failed: {fallback_reason}",
            file=sys.stderr,
        )


def main() -> int:
    _install_rtlsdr_fallback()
    import main as fm_main

    return fm_main.main()


if __name__ == "__main__":
    raise SystemExit(main())
