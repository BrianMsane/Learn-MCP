import logging
import sys

logger = logging.getLogger("MCPClient")
logger.setLevel(logging.DEBUG)

# file handler with debug leve

file_handler = logging.FileHandler("mcp_client.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(messages)s")
)
logger.addHandler(file_handler)

# console hander with info level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(messages)s")
)
logger.addHandler(console_handler)
