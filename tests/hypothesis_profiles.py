"""
Hypothesis test profiles for different environments.

Usage:
    HYPOTHESIS_PROFILE=ci pytest tests/property/
    HYPOTHESIS_PROFILE=exhaustive pytest tests/property/
"""
import os
from hypothesis import settings, Verbosity, Phase, HealthCheck

# =============================================================================
# CI Profile - Thorough but time-bounded
# =============================================================================
settings.register_profile(
    "ci",
    max_examples=500,
    deadline=None,  # Disable deadline in CI (can be slow)
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
    ],
    verbosity=Verbosity.normal,
    phases=[Phase.generate, Phase.target, Phase.shrink],
    derandomize=False,
    print_blob=True,  # Print seed for reproduction
)

# =============================================================================
# Development Profile - Fast feedback loop
# =============================================================================
settings.register_profile(
    "dev",
    max_examples=50,
    deadline=1000,  # 1 second deadline
    verbosity=Verbosity.verbose,
    phases=[Phase.generate, Phase.shrink],
    derandomize=False,
)

# =============================================================================
# Debug Profile - Minimal examples, maximum verbosity
# =============================================================================
settings.register_profile(
    "debug",
    max_examples=10,
    deadline=None,
    verbosity=Verbosity.debug,
    phases=[Phase.generate, Phase.shrink],
    derandomize=True,  # Reproducible for debugging
)

# =============================================================================
# Exhaustive Profile - For release testing
# =============================================================================
settings.register_profile(
    "exhaustive",
    max_examples=10000,
    deadline=None,
    verbosity=Verbosity.quiet,
    phases=[Phase.generate, Phase.target, Phase.shrink],
    stateful_step_count=100,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.large_base_example,
    ],
)

# =============================================================================
# Nightly Profile - Even more thorough, for nightly CI
# =============================================================================
settings.register_profile(
    "nightly",
    max_examples=50000,
    deadline=None,
    verbosity=Verbosity.quiet,
    phases=[Phase.generate, Phase.target, Phase.shrink],
    stateful_step_count=200,
    suppress_health_check=list(HealthCheck),
)

# =============================================================================
# Load profile based on environment
# =============================================================================
_profile = os.getenv("HYPOTHESIS_PROFILE", "dev")
settings.load_profile(_profile)

print(f"Hypothesis profile: {_profile}")
