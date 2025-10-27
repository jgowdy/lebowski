"""
Flag normalization and conflict resolution.

Handles combining compiler flags from multiple sources (config, parent opinion, child opinion)
and resolves conflicts intelligently.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class FlagConflict:
    """Represents a conflict between flags"""
    flag_type: str  # e.g., "optimization", "march", "std"
    old_value: str  # e.g., "-O2"
    new_value: str  # e.g., "-O3"
    source: str     # e.g., "child opinion", "parent opinion", "config"


@dataclass
class NormalizationResult:
    """Result of flag normalization"""
    flags: List[str]
    conflicts: List[FlagConflict] = field(default_factory=list)
    duplicates_removed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FlagNormalizer:
    """
    Normalize and deduplicate compiler flags.

    Handles conflicts intelligently:
    - Later flags override earlier flags (child > parent > config)
    - Duplicates are removed
    - Conflicting flags are detected and reported
    """

    # Flag patterns that conflict with each other
    CONFLICT_PATTERNS = {
        'optimization': re.compile(r'^-O[0-3sgz]$'),
        'march': re.compile(r'^-march=(.+)$'),
        'mtune': re.compile(r'^-mtune=(.+)$'),
        'std': re.compile(r'^-std=(.+)$'),
        'fpic': re.compile(r'^-f(pic|PIC|pie|PIE)$'),
        'lto': re.compile(r'^-flto(=.*)?$'),
        'stack_protector': re.compile(r'^-fstack-protector(-strong|-all)?$'),
        'fortify_source': re.compile(r'^-D_FORTIFY_SOURCE=[0-9]$'),
        'visibility': re.compile(r'^-fvisibility=(.+)$'),
        'exceptions': re.compile(r'^-f(no-)?exceptions$'),
        'rtti': re.compile(r'^-f(no-)?rtti$'),
        'omit_frame_pointer': re.compile(r'^-f(no-)?omit-frame-pointer$'),
    }

    # Linker-specific patterns
    LD_CONFLICT_PATTERNS = {
        'rpath': re.compile(r'^-Wl,-rpath=(.+)$'),
        'dynamic_linker': re.compile(r'^-Wl,--dynamic-linker=(.+)$'),
        'soname': re.compile(r'^-Wl,-soname[,=](.+)$'),
        'strip': re.compile(r'^-Wl,(-s|--strip-all|--strip-debug)$'),
    }

    @staticmethod
    def normalize_cflags(sources: List[Tuple[str, List[str]]], verbose: bool = False) -> NormalizationResult:
        """
        Normalize CFLAGS from multiple sources.

        Args:
            sources: List of (source_name, flags) tuples in precedence order
                     (lowest to highest precedence)
            verbose: If True, report all conflicts

        Returns:
            NormalizationResult with normalized flags and diagnostics
        """
        result = NormalizationResult(flags=[])
        seen = set()
        flag_owners: Dict[str, Tuple[str, str]] = {}  # flag_type -> (value, source)

        # Process flags in order (low to high precedence)
        for source_name, flags in sources:
            for flag in flags:
                # Check for conflicts
                conflict_type = FlagNormalizer._get_conflict_type(flag)

                if conflict_type:
                    # This flag conflicts with a category
                    if conflict_type in flag_owners:
                        old_value, old_source = flag_owners[conflict_type]
                        if old_value != flag:
                            # Conflict detected
                            result.conflicts.append(FlagConflict(
                                flag_type=conflict_type,
                                old_value=old_value,
                                new_value=flag,
                                source=source_name
                            ))
                        else:
                            # Same value, just a duplicate
                            result.duplicates_removed.append(flag)

                    # Update owner (later source wins)
                    flag_owners[conflict_type] = (flag, source_name)
                else:
                    # Non-conflicting flag - just deduplicate
                    if flag in seen:
                        result.duplicates_removed.append(flag)
                    else:
                        seen.add(flag)

        # Build final flag list from owners (preserves order of first appearance)
        for source_name, flags in sources:
            for flag in flags:
                conflict_type = FlagNormalizer._get_conflict_type(flag)

                if conflict_type:
                    # Only add if this is the winning value
                    if flag_owners[conflict_type][0] == flag and flag not in result.flags:
                        result.flags.append(flag)
                else:
                    # Non-conflicting flag
                    if flag not in result.flags:
                        result.flags.append(flag)

        # Generate warnings for conflicts
        for conflict in result.conflicts:
            result.warnings.append(
                f"{conflict.flag_type}: {conflict.old_value} overridden by {conflict.new_value} (from {conflict.source})"
            )

        return result

    @staticmethod
    def normalize_ldflags(sources: List[Tuple[str, List[str]]], verbose: bool = False) -> NormalizationResult:
        """
        Normalize LDFLAGS from multiple sources.

        Similar to normalize_cflags but handles linker-specific flags.
        """
        result = NormalizationResult(flags=[])
        seen = set()
        flag_owners: Dict[str, Tuple[str, str]] = {}

        # Process flags in order (low to high precedence)
        for source_name, flags in sources:
            for flag in flags:
                # Check for linker conflicts
                conflict_type = FlagNormalizer._get_ld_conflict_type(flag)

                if conflict_type:
                    if conflict_type in flag_owners:
                        old_value, old_source = flag_owners[conflict_type]
                        if old_value != flag:
                            result.conflicts.append(FlagConflict(
                                flag_type=conflict_type,
                                old_value=old_value,
                                new_value=flag,
                                source=source_name
                            ))
                        else:
                            result.duplicates_removed.append(flag)

                    flag_owners[conflict_type] = (flag, source_name)
                else:
                    # Non-conflicting linker flag
                    if flag in seen:
                        result.duplicates_removed.append(flag)
                    else:
                        seen.add(flag)

        # Build final flag list
        for source_name, flags in sources:
            for flag in flags:
                conflict_type = FlagNormalizer._get_ld_conflict_type(flag)

                if conflict_type:
                    if flag_owners[conflict_type][0] == flag and flag not in result.flags:
                        result.flags.append(flag)
                else:
                    if flag not in result.flags:
                        result.flags.append(flag)

        # Generate warnings
        for conflict in result.conflicts:
            result.warnings.append(
                f"{conflict.flag_type}: {conflict.old_value} overridden by {conflict.new_value} (from {conflict.source})"
            )

        return result

    @staticmethod
    def _get_conflict_type(flag: str) -> Optional[str]:
        """Get conflict type for a compiler flag, or None if no conflicts"""
        for conflict_type, pattern in FlagNormalizer.CONFLICT_PATTERNS.items():
            if pattern.match(flag):
                return conflict_type
        return None

    @staticmethod
    def _get_ld_conflict_type(flag: str) -> Optional[str]:
        """Get conflict type for a linker flag, or None if no conflicts"""
        for conflict_type, pattern in FlagNormalizer.LD_CONFLICT_PATTERNS.items():
            if pattern.match(flag):
                return conflict_type
        return None

    @staticmethod
    def explain_flags(flags: List[str]) -> Dict[str, List[str]]:
        """
        Categorize flags for display.

        Returns a dict of category -> [flags]
        """
        categories = {
            'optimization': [],
            'architecture': [],
            'security': [],
            'debugging': [],
            'linking': [],
            'standards': [],
            'warnings': [],
            'defines': [],
            'includes': [],
            'other': [],
        }

        for flag in flags:
            if re.match(r'^-O[0-3sgz]$', flag):
                categories['optimization'].append(flag)
            elif re.match(r'^-march=|^-mtune=|^-mcpu=', flag):
                categories['architecture'].append(flag)
            elif re.match(r'^-fstack-protector|^-D_FORTIFY_SOURCE|^-fPIE|^-fpie', flag):
                categories['security'].append(flag)
            elif re.match(r'^-g|^-ggdb', flag):
                categories['debugging'].append(flag)
            elif flag.startswith('-Wl,') or flag.startswith('-l') or flag.startswith('-L'):
                categories['linking'].append(flag)
            elif re.match(r'^-std=', flag):
                categories['standards'].append(flag)
            elif flag.startswith('-W'):
                categories['warnings'].append(flag)
            elif flag.startswith('-D'):
                categories['defines'].append(flag)
            elif flag.startswith('-I'):
                categories['includes'].append(flag)
            else:
                categories['other'].append(flag)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    @staticmethod
    def validate_flags(flags: List[str]) -> List[str]:
        """
        Validate flags and return warnings about potentially problematic combinations.
        """
        warnings = []

        # Check for LTO without optimization
        has_lto = any(flag.startswith('-flto') for flag in flags)
        has_optimization = any(re.match(r'^-O[1-3]$', flag) for flag in flags)
        if has_lto and not has_optimization:
            warnings.append("LTO enabled without optimization (-O1/-O2/-O3) - may not be effective")

        # Check for conflicting frame pointer settings
        has_omit = '-fomit-frame-pointer' in flags
        has_no_omit = '-fno-omit-frame-pointer' in flags
        if has_omit and has_no_omit:
            warnings.append("Both -fomit-frame-pointer and -fno-omit-frame-pointer present")

        # Check for PIE with wrong optimization
        has_pie = any(flag in ['-fPIE', '-fpie'] for flag in flags)
        has_pic = any(flag in ['-fPIC', '-fpic'] for flag in flags)
        if has_pie and has_pic:
            warnings.append("Both PIE and PIC flags present - PIE is more restrictive")

        # Check for multiple fortify levels
        fortify_flags = [f for f in flags if f.startswith('-D_FORTIFY_SOURCE=')]
        if len(fortify_flags) > 1:
            warnings.append(f"Multiple FORTIFY_SOURCE levels: {fortify_flags}")

        return warnings
