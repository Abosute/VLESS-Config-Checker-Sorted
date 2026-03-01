import httpx
import asyncio
from httpx import HTTPStatusError
from loguru import logger
from enum import Enum
from typing import Optional

class LogMessage(Enum):
    SUCCESS = 'Success'
    INVALID_LINK = 'Invalid link'
    TYPE_ERROR = "The link must be a string"
    UNEXPECTED = "Unexpected error {}"
    HTTPERROR = 'HTTPStatusError {}'
    EMPTY_FILES = 'Empty files'

class VlessParse:
    pass