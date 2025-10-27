#!/usr/bin/env python3
"""Production-ready Boston OpenData MCP server with graceful startup/shutdown."""

import asyncio
import signal
import sys
import time
from typing import Optional

from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from .server import app, perform_health_check, get_server_status
from .ckan import close_http_client
from .utils.logger import get_logger, setup_logging
from .config import settings
from .utils.exceptions import ConfigurationError


# Global shutdown event
_shutdown_event = asyncio.Event()
_startup_time = None


async def startup() -> None:
    """Perform startup tasks."""
    global _startup_time
    _startup_time = time.time()

    logger = get_logger("main")
    logger.info(
        "Starting Boston Open Data MCP Server",
        extra={
            "version": "1.0.0",
            "environment": settings.environment,
            "debug": settings.debug,
        },
    )

    try:
        # Validate configuration
        if not settings.ckan_base_url:
            raise ConfigurationError("CKAN base URL is required")

        # Perform initial health check
        logger.info("Performing initial health check...")
        health_status = await perform_health_check()

        if health_status["status"] != "healthy":
            logger.warning(
                "Initial health check failed", extra={"health_status": health_status}
            )
        else:
            logger.info("Initial health check passed")

        logger.info("Server startup completed successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


async def shutdown() -> None:
    """Perform graceful shutdown tasks."""
    logger = get_logger("main")
    logger.info("Starting graceful shutdown...")

    try:
        # Close HTTP client
        await close_http_client()

        # Log final status
        if _startup_time:
            uptime = time.time() - _startup_time
            logger.info(f"Server shutdown completed. Uptime: {uptime:.2f} seconds")
        else:
            logger.info("Server shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


def signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handle shutdown signals."""
    logger = get_logger("main")
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name} signal, initiating shutdown...")
    _shutdown_event.set()


async def health_check_loop() -> None:
    """Background health check loop."""
    logger = get_logger("health")

    while not _shutdown_event.is_set():
        try:
            await asyncio.sleep(settings.health_check_interval)

            if not _shutdown_event.is_set():
                health_status = await perform_health_check()

                if health_status["status"] != "healthy":
                    logger.warning(
                        "Health check failed", extra={"health_status": health_status}
                    )
                else:
                    logger.debug("Health check passed")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Health check loop error: {e}", exc_info=True)


async def main() -> None:
    """Start the Boston Open Data MCP server with graceful startup/shutdown."""
    logger = setup_logging(
        level=settings.log_level,
        format_type=settings.log_format,
        include_extra=settings.log_include_extra,
    )

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Perform startup tasks
        await startup()

        # Start health check loop
        health_task = asyncio.create_task(health_check_loop())

        try:
            # Start the MCP server
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP server started, waiting for connections...")

                # Run the server until shutdown is requested
                server_task = asyncio.create_task(
                    app.run(
                        read_stream,
                        write_stream,
                        InitializationOptions(
                            server_name="boston-opendata-server",
                            server_version="1.0.0",
                            capabilities=app.get_capabilities(
                                notification_options=NotificationOptions(),
                                experimental_capabilities={},
                            ),
                        ),
                    )
                )

                # Wait for either shutdown signal or server completion
                done, pending = await asyncio.wait(
                    [server_task, asyncio.create_task(_shutdown_event.wait())],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # Check if server task completed with an error
                if server_task in done:
                    try:
                        await server_task
                    except Exception as e:
                        logger.error(f"Server task failed: {e}", exc_info=True)
                        raise

        finally:
            # Cancel health check task
            health_task.cancel()
            try:
                await health_task
            except asyncio.CancelledError:
                pass

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
        raise
    finally:
        # Perform shutdown tasks
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Server crashed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
