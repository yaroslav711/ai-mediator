"""
Main Bot application entry point.
"""

import asyncio
import time


async def main():
    """Main bot function."""
    print("🤖 Bot started successfully!")
    print("Bot would be listening for Telegram messages...")
    
    # Keep the container running
    while True:
        await asyncio.sleep(10)
        print("✅ Bot is healthy")


if __name__ == "__main__":
    asyncio.run(main())
