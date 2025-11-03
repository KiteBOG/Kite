class _Log:
    def info(self, msg: str, **kwargs):
        parts = [msg] + [f"{k}={v}" for k, v in kwargs.items()]
        print("[Kite] " + ", ".join(parts))

    def warn(self, msg: str, **kwargs):
        parts = [msg] + [f"{k}={v}" for k, v in kwargs.items()]
        print("[Kite:WARN] " + ", ".join(parts))

    def error(self, msg: str, **kwargs):
        parts = [msg] + [f"{k}={v}" for k, v in kwargs.items()]
        print("[Kite:ERROR] " + ", ".join(parts))

log = _Log()
