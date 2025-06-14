#!/usr/bin/env python3
"""
Version Manager for Loggamera Integration

Utility to manage version bumping and release preparation.

Usage:
  python tools/version_manager.py current
  python tools/version_manager.py bump patch
  python tools/version_manager.py bump minor
  python tools/version_manager.py bump major
  python tools/version_manager.py set 1.2.3
"""

import argparse
import json
import os
import sys
from pathlib import Path

MANIFEST_PATH = "custom_components/loggamera/manifest.json"


def get_current_version():
    """Get the current version from manifest.json."""
    try:
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
            return manifest.get("version", "0.0.0")
    except FileNotFoundError:
        print(f"Error: {MANIFEST_PATH} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {MANIFEST_PATH}")
        sys.exit(1)


def set_version(new_version):
    """Set a new version in manifest.json."""
    try:
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)

        manifest["version"] = new_version

        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")  # Add trailing newline

        print(f"Version updated to {new_version}")
        return True
    except Exception as e:
        print(f"Error updating version: {e}")
        return False


def parse_version(version_str):
    """Parse a version string into major, minor, patch components."""
    try:
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError("Version must have exactly 3 parts")

        major, minor, patch = map(int, parts)
        return major, minor, patch
    except ValueError as e:
        print(f"Error parsing version '{version_str}': {e}")
        sys.exit(1)


def bump_version(current_version, bump_type):
    """Bump version according to type (major, minor, patch)."""
    major, minor, patch = parse_version(current_version)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"Error: Invalid bump type '{bump_type}'. Use: major, minor, or patch")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def validate_version_format(version):
    """Validate that version follows semantic versioning format."""
    try:
        major, minor, patch = parse_version(version)
        if major < 0 or minor < 0 or patch < 0:
            raise ValueError("Version components must be non-negative")
        return True
    except ValueError as e:
        print(f"Error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage Loggamera integration version")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Current version command
    subparsers.add_parser("current", help="Show current version")

    # Bump version command
    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument(
        "type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    bump_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what the new version would be without changing it",
    )

    # Set version command
    set_parser = subparsers.add_parser("set", help="Set specific version")
    set_parser.add_argument("version", help="Version to set (e.g., 1.2.3)")
    set_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate version format without changing it",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate version format")
    validate_parser.add_argument("version", help="Version to validate")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Ensure we're in the right directory
    if not os.path.exists(MANIFEST_PATH):
        print(
            f"Error: {MANIFEST_PATH} not found. Run this script from the repository root."
        )
        sys.exit(1)

    if args.command == "current":
        current = get_current_version()
        print(f"Current version: {current}")

    elif args.command == "bump":
        current = get_current_version()
        new_version = bump_version(current, args.type)

        if args.dry_run:
            print(f"Current version: {current}")
            print(f"New version would be: {new_version}")
        else:
            if set_version(new_version):
                print(f"Bumped version from {current} to {new_version}")

    elif args.command == "set":
        if not validate_version_format(args.version):
            sys.exit(1)

        current = get_current_version()

        if args.dry_run:
            print(f"Current version: {current}")
            print(f"Version would be set to: {args.version}")
        else:
            if set_version(args.version):
                print(f"Changed version from {current} to {args.version}")

    elif args.command == "validate":
        if validate_version_format(args.version):
            print(f"✅ Version format is valid: {args.version}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
