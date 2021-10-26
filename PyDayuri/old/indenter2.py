"Provides Indentation services for languages with indentation similar to Haskell"

from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple, Dict, Optional
from enum import Enum, auto
import logging


from lark import logger
from lark.exceptions import LarkError
from lark.lark import PostLex
from lark.lexer import Token

log =logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
log_format = logging.Formatter("%(filename)s-%(funcName)s-%(lineno)d: %(message)s")
log_handler.setFormatter(log_format)
log.addHandler(log_handler)

logb = log.debug

class Request(Enum):
    at_start = auto()
    at_end = auto()
    at_next = auto()
    

class Indentation():
    def __init__(self, requested_by:Token, request:Request , being_at_token:Token, end_type:str)->None:
        self.requested_by = requested_by
