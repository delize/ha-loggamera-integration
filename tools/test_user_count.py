#!/usr/bin/env python3
"""Test script to check user count functionality."""

import json

import requests

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://platform.loggamera.se/api/v2"


def test_user_count():
    """Test user count fields in Organizations API."""
    print("🔧 Testing User Count Functionality")
    print("=" * 50)

    # Test Organizations endpoint for user data
    print("📡 Fetching Organizations data...")
    org_response = requests.post(
        f"{BASE_URL}/Organizations",
        json={"ApiKey": API_KEY},
        headers={"Content-Type": "application/json"},
    )

    if org_response.status_code == 200:
        org_data = org_response.json()
        organizations = org_data.get("Data", {}).get("Organizations", [])

        print(f"✅ Found {len(organizations)} organizations")
        print("\n📊 Organization User Data:")

        for org in organizations:
            org_id = org["Id"]
            org_name = org["Name"]
            parent_id = org["ParentId"]
            user_count = org.get("UserCount")
            member_count = org.get("MemberCount")

            parent_info = f" (Parent: {parent_id})" if parent_id != 0 else " (Root)"

            print(f"\n  🏢 {org_name} (ID: {org_id}){parent_info}")
            print(f"    👤 UserCount: {user_count}")
            print(f"    👥 MemberCount: {member_count}")

            # Check if we have any actual user data
            if user_count is not None and user_count > 0:
                print(f"    ✅ Found {user_count} users!")
            elif user_count is None:
                print(f"    ⚠️  UserCount is null (may need time to populate)")
            else:
                print(f"    ℹ️  No users yet (count is 0)")

            if member_count is not None and member_count > 0:
                print(f"    ✅ Found {member_count} members!")
            elif member_count is None:
                print(f"    ⚠️  MemberCount is null (may need time to populate)")
            else:
                print(f"    ℹ️  No members yet (count is 0)")

        # Test what our integration will show
        print(f"\n🔧 Integration Behavior:")
        for org in organizations:
            org_id = org["Id"]
            user_count = org.get("UserCount")
            member_count = org.get("MemberCount")

            # This is how our integration handles null values
            user_count_value = user_count if user_count is not None else 0
            member_count_value = member_count if member_count is not None else 0

            print(
                f"  Org {org_id}: user_count sensor = {user_count_value}, member_count sensor = {member_count_value}"
            )

        print(f"\n💡 Notes:")
        print(f"  - User count sensors created for all organizations")
        print(f"  - null values show as 0 until API provides data")
        print(f"  - Sensors will automatically update when API returns real counts")
        print(f"  - This future-proofs the integration for user management features")

        return True
    else:
        print(f"❌ Failed to get organizations: {org_response.status_code}")
        return False


if __name__ == "__main__":
    test_user_count()
