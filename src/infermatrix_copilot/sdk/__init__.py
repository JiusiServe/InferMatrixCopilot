"""Stable Python SDK for embedded InferMatrixCopilot consumers.

Only versioned namespaces are public.  Keep this package initializer lazy so
``import infermatrix_copilot.sdk`` never imports a server or initializes a
runtime as a side effect.  Python loads ``sdk.v1`` normally when a consumer
imports that versioned namespace.
"""

__all__ = ["v1"]
