import asyncio

import uvicorn

from .bot import bot, dp
from .config import PORT
from .main import app


async def run_bot():
    await dp.start_polling(bot)


async def run_web():
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(run_bot(), run_web())


if __name__ == "__main__":
    asyncio.run(main())
