"""
bbbkit.druggability — Backward compatibility shim.
Redirects all imports to the top-level `druggability` package.
"""

from druggability import *  # noqa: F401, F403
import druggability as _d

# Re-export internal helpers for backward compatibility with existing tests
_compute_composite = getattr(_d, "_compute_composite", None)
_resolve_structure_input = getattr(_d, "_resolve_structure_input", None)
_resolve_tractability_score = getattr(_d, "_resolve_tractability_score", None)
_resolve_ligandability_score = getattr(_d, "_resolve_ligandability_score", None)
_resolve_structure_score = getattr(_d, "_resolve_structure_score", None)
