"""
Run this script to create or reset the admin user.
Usage:
    .venv\Scripts\python create_admin.py
"""
import asyncio
import sys
import bcrypt
from app.database import init_db
from app.models.models import User


async def main():
    await init_db()

    print("=== Admin User Setup ===\n")

    username = input("Enter username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    password = input("Enter password: ").strip()
    if len(password) < 6:
        print("Password must be at least 6 characters.")
        sys.exit(1)

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    existing = await User.find_one(User.username == username)
    if existing:
        existing.hashed_password = hashed
        await existing.save()
        print(f"\n✓ Password updated for user '{username}'")
    else:
        # Delete any previous admin if replacing
        all_users = await User.find().to_list()
        if all_users:
            confirm = input(f"\n{len(all_users)} user(s) already exist. Replace all with new admin? (yes/no): ").strip()
            if confirm.lower() != "yes":
                print("Aborted.")
                sys.exit(0)
            for u in all_users:
                await u.delete()
            print("Existing users deleted.")

        user = User(username=username, hashed_password=hashed)
        await user.insert()
        print(f"\n✓ Admin user '{username}' created successfully.")

    print("\nYou can now log in at http://localhost:5173")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)}")


if __name__ == "__main__":
    asyncio.run(main())
