#!/usr/bin/env python3
"""
User Creation and Sign-In Script for Crater Clone Backend

This script allows you to:
1. Create a new user in the database
2. Sign in an existing user and get a JWT token

Usage:
    python create_user_and_signin.py create --email admin@example.com --password securepassword123 --name "Admin User"
    python create_user_and_signin.py signin --email admin@example.com --password securepassword123
    python create_user_and_signin.py create_or_signin --email admin@example.com --password securepassword123 --name "Admin User"

The last command (create_or_signin) will create the user if they don't exist, or sign them in if they do.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password, verify_password, create_access_token
from app.database import Base
from app.models.user import User
from app.config import settings


def get_engine():
    """Get database engine, falling back to SQLite if PostgreSQL is unavailable."""
    # Always use SQLite for standalone usage (no PostgreSQL dependency)
    sqlite_url = "sqlite+aiosqlite:///./crater_users.db"
    engine = create_async_engine(sqlite_url, echo=False)
    return engine, sqlite_url


async def init_db(engine):
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_user(
    email: str,
    password: str,
    name: str,
    phone: str | None = None,
    role: str = "admin",
) -> User:
    """Create a new user in the database."""
    
    engine, db_url = get_engine()
    await init_db(engine)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user already exists
        existing_user = await session.scalar(select(User).where(User.email == email))
        if existing_user:
            print(f"⚠️  User with email '{email}' already exists!")
            return existing_user
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Create new user
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            password=hashed_password,
            role=role,
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        print(f"✅ User created successfully!")
        print(f"   ID: {new_user.id}")
        print(f"   Name: {new_user.name}")
        print(f"   Email: {new_user.email}")
        print(f"   Role: {new_user.role}")
        
        return new_user


async def sign_in_user(email: str, password: str) -> str | None:
    """Sign in a user and return JWT token."""
    
    engine, db_url = get_engine()
    await init_db(engine)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find user by email
        user = await session.scalar(select(User).where(User.email == email))
        
        if not user:
            print(f"❌ No user found with email: {email}")
            return None
        
        if not user.password:
            print(f"❌ User exists but has no password set. Please reset password.")
            return None
        
        # Verify password
        if not verify_password(password, user.password):
            print(f"❌ Invalid password for user: {email}")
            return None
        
        # Generate JWT token
        token = create_access_token(subject=user.id)
        
        print(f"✅ Sign in successful!")
        print(f"   User ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"\n🔑 JWT Token:")
        print(f"   {token}")
        print(f"\n📝 Use this token in the Authorization header:")
        print(f"   Authorization: Bearer {token}")
        
        return token


async def create_or_signin(email: str, password: str, name: str, phone: str | None = None):
    """Create user if doesn't exist, otherwise sign them in."""
    
    engine, db_url = get_engine()
    await init_db(engine)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.email == email))
        
        if not user:
            print("📝 User not found. Creating new user...")
            
            # Create user
            hashed_password = hash_password(password)
            new_user = User(
                name=name,
                email=email,
                phone=phone,
                password=hashed_password,
                role="admin",
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"✅ User created successfully!")
            print(f"   ID: {new_user.id}")
            print(f"   Name: {new_user.name}")
            print(f"   Email: {new_user.email}")
            
            # Now generate token
            token = create_access_token(subject=new_user.id)
            print(f"\n🔑 JWT Token:")
            print(f"   {token}")
            print(f"\n📝 Use this token in the Authorization header:")
            print(f"   Authorization: Bearer {token}")
            return token
        else:
            print("📝 User found. Signing in...")
            
            if not user.password:
                print(f"❌ User exists but has no password set.")
                return None
            
            if not verify_password(password, user.password):
                print(f"❌ Invalid password.")
                return None
            
            token = create_access_token(subject=user.id)
            print(f"✅ Sign in successful!")
            print(f"   User ID: {user.id}")
            print(f"   Name: {user.name}")
            print(f"   Email: {user.email}")
            print(f"\n🔑 JWT Token:")
            print(f"   {token}")
            print(f"\n📝 Use this token in the Authorization header:")
            print(f"   Authorization: Bearer {token}")
            return token


def main():
    parser = argparse.ArgumentParser(
        description="Create users and sign in for Crater Clone Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new admin user
  python %(prog)s create --email admin@example.com --password mypassword123 --name "Admin User"
  
  # Sign in an existing user
  python %(prog)s signin --email admin@example.com --password mypassword123
  
  # Create user if not exists, or sign in if exists (convenient for setup)
  python %(prog)s create_or_signin --email admin@example.com --password mypassword123 --name "Admin User"
  
  # Create a regular user
  python %(prog)s create --email user@example.com --password mypassword123 --name "John Doe" --role user
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("--email", required=True, help="User email address")
    create_parser.add_argument("--password", required=True, help="User password")
    create_parser.add_argument("--name", required=True, help="User full name")
    create_parser.add_argument("--phone", help="User phone number (optional)")
    create_parser.add_argument("--role", default="admin", choices=["admin", "user"], help="User role (default: admin)")
    
    # Sign in command
    signin_parser = subparsers.add_parser("signin", help="Sign in an existing user")
    signin_parser.add_argument("--email", required=True, help="User email address")
    signin_parser.add_argument("--password", required=True, help="User password")
    
    # Create or sign in command
    create_or_signin_parser = subparsers.add_parser("create_or_signin", help="Create user if not exists, or sign in if exists")
    create_or_signin_parser.add_argument("--email", required=True, help="User email address")
    create_or_signin_parser.add_argument("--password", required=True, help="User password")
    create_or_signin_parser.add_argument("--name", required=True, help="User full name (used only if creating)")
    create_or_signin_parser.add_argument("--phone", help="User phone number (optional)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print(f"\n🚀 Crater Clone - User Management\n")
    print(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")
    print("-" * 50)
    
    if args.command == "create":
        user = asyncio.run(create_user(
            email=args.email,
            password=args.password,
            name=args.name,
            phone=args.phone,
            role=args.role,
        ))
        if user:
            print(f"\n💡 To sign in, run:")
            print(f"   python {sys.argv[0]} signin --email {args.email} --password <password>")
    
    elif args.command == "signin":
        token = asyncio.run(sign_in_user(
            email=args.email,
            password=args.password,
        ))
        if not token:
            sys.exit(1)
    
    elif args.command == "create_or_signin":
        token = asyncio.run(create_or_signin(
            email=args.email,
            password=args.password,
            name=args.name,
            phone=args.phone,
        ))
        if not token:
            sys.exit(1)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
