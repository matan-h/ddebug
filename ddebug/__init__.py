try:
    from .dd_class import dd, ClsDebugger, set_excepthook,set_atexit
except ImportError:
    from dd_class import dd, ClsDebugger, set_excepthook,set_atexit

__all__ = ["dd", "ClsDebugger", "set_excepthook", "set_atexit"]
