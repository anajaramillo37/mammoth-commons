from mai import backend

try:
    from mai import states
    from mai import bias
except ImportError:
    print("Failed to import MAI-Bias frontend (you are probably lacking a graphics environment)")

