# AgentConnect: https://github.com/agent-network-protocol/AgentConnect
# Author: GaoWei Chang
# Email: chgaowei@gmail.com
# Website: https://agent-network-protocol.com/
#
# This project is open-sourced under the MIT License. For details, please see the LICENSE file.

# Configuration file for tests
import os
from pathlib import Path

from dotenv import load_dotenv

# Get the project root directory (assuming tests folder is directly under root)
# ROOT_DIR = Path(__file__).parent.parent.parent
ROOT_DIR = Path(__file__).parent

# Load environment variables from root .env file
load_dotenv(ROOT_DIR / ".env")

# OpenRouter - DeepSeek API configurations
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
DASHSCOPE_MODEL_NAME = os.getenv("DASHSCOPE_MODEL_NAME")


def validate_config():
    """Validate that all required environment variables are set"""
    required_vars = ["DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL", "DASHSCOPE_MODEL_NAME"]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
