"Provides Indentation services for languages with indentation similar to Haskell"

from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple, Dict, Optional, Union
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

class IndenterException(Exception):
    pass

class IndentationStackException(IndenterException):
    pass

class BadCompare(IndentationStackException):
    pass

class BadAppend(IndentationStackException):
    pass

class BadIndentationLevel(IndentationStackException):
    
    def __init__(self, item:"IndentationItem"):
        super().__init__(f"Indentation level must be greater than zero, given {item}")


class StartIndentAt(Enum):
    _start = auto()
    _end = auto()
    _next = auto()

class PendingTask(Enum):
    make_closable =  auto()
    make_non_closable = auto()
    nothing = auto()
    
def token_repr(token:Token)->str:
    return f"Token(type={token.type},value={token.value},line={token.line},column={token.column})"

def token_str(token:Token)->str:
    return repr(token)

def token_error(token:Token)->str:
    return f"{token.value} at line {token.line}, column {token.column}"

class IndentErrorToken(Token):
    found_token : Token
    stack_item : Optional["IndentationItem"]
    token_msg : str
    item_msg : Optional[str]
    end_msg : Optional[str]
    
    def __init__(self, found_token: Token, stack_item: Optional["IndentationItem"], token_msg:str, item_msg:Optional[str], end_msg:Optional[str])->None:
        super().__init__("IndentErrorToken","")
        self.found_token = found_token
        self.stack_item = stack_item
        self.token_msg = token_msg
        self.item_msg = item_msg
        self.end_msg = end_msg


class Dedent():
    start :"IndentationItem"
    end : Token

    def __init__(self, indentation_start:"IndentationItem", end_token:Token)->None:
        self.start = indentation_start
        self.end = end_token

class IndentationItem():
    request_by:Token
    start_at: StartIndentAt
    begins_at: Token
    close_at_type:Optional[str]
    level:int
    is_closable: bool

    def __init__(self, request_by:Token, start_at:StartIndentAt , begins_at:Token, close_at_type:Optional[str]=None)->None:
        self.request_by = request_by
        self.start_at = start_at
        self.begins_at = begins_at
        self.close_at_type = close_at_type
        self.is_closable = close_at_type is not None

        self.set_level()

    def set_level(self):
        if self.start_at == StartIndentAt._start:
            self.level = self.request_by.column
        elif self.start_at == StartIndentAt._end:
            self.level = self.request_by.end_column
        else :
            self.level = self.begins_at.column

    def is_match(self, token:Token):
        if self.is_closable:
            return self.close_at_type == token.type
        return False


    def error_msg(self):
        msg = f"{self.request_by.value} at line {self.request_by.line}, column {self.request_by.column} started at {self.begins_at.value} in "
        msg += f"line {self.begins_at.line}, column {self.begins_at.column}"
        return  msg

    def __str__(self):
        return f"Indentation({self.level}, {self.request_by}, {self.start_at}, {self.begins_at}, {self.close_at_type})"

    def __repr__(self):
        return f"Indentation({self.level}, {token_repr(self.request_by)}, {self.start_at}, {token_repr(self.begins_at)}, {self.close_at_type}, {self.is_closable})"
        
    def __lt__(self, other: Union["IndentationItem", int])->bool:
        if isinstance(other, IndentationItem):
            return self.level < other.level
        elif isinstance(other, int):
            return self.level < other
        else :
            raise BadCompare("IndentationItem can only be compared to IndentationItem or int")

    def __le__(self, other: Union["IndentationItem", int])->bool:
        if isinstance(other, IndentationItem):
            return self.level <= other.level
        elif isinstance(other, int):
            return self.level <= other
        else :
            raise BadCompare("IndentationItem can only be compared to IndentationItem or int")


    def __gt__(self, other: Union["IndentationItem", int])->bool:
        if isinstance(other, IndentationItem):
            return self.level > other.level
        elif isinstance(other, int):
            return self.level > other
        else :
            raise BadCompare("IndentationItem can only be compared to IndentationItem or int")

    def __ge__(self, other: Union["IndentationItem", int])->bool:
        if isinstance(other, IndentationItem):
            return self.level >= other.level
        elif isinstance(other, int):
            return self.level >= other
        else :
            raise BadCompare("IndentationItem can only be compared to IndentationItem or int")

    def __eq__(self, other)->bool:
        if isinstance(other, IndentationItem):
            return self.request_by == other.request_by and  \
                self.start_at == other.start_at and \
                self.begins_at == other.begins_at and \
                self.close_at_type == other.close_at_type and  \
                self.level == other.level
        elif isinstance(other, int):
            return self.level == other
        else :
            raise BadCompare("IndentationItem can only be compared to IndentationItem or int")

class State():
    pending : PendingTask
    stack : List[IndentationItem]
        
    def is_valid_level(self, item:Union[IndentationItem,int])->bool:
        return item >0

    def is_appendable(self, item:Union[IndentationItem, int])->bool:
        if not self.is_valid_level(item):
            return False

        if len(self.stack)==0:
            return True

        last = self.stack[-1]

        return last>item

    def safe_append(self, item:IndentationItem)->bool:
        if self.is_appendable(item):
            self.stack.append(item)
            return True
        return False

    def append(self, item:IndentationItem)->None:
        if self.is_appendable(item):
            self.stack.append(item)
        raise BadAppend()

    def __str__(self):
        pending = str(self.pending)
        converted_stack = [str(item) for item in self.stack ]
        stack = "\n    ".join(converted_stack)
        return f"{pending} \n    [\n    {stack},\n    ]"

    def __repr__(self):
        pending = str(self.pending)
        converted_stack = [repr(item) for item in self.stack ]
        stack = "\n    ".join(converted_stack)
        return f"{pending} \n    [\n    {stack},\n    ]"


    def maybe_pop(self, token:Token)->List[Union[Dedent,IndentErrorToken]]:

        if self.is_appendable(token.column):
            return []

        poped_items: List[Union[Dedent,IndentErrorToken]] = []
        while len(self.stack) != 0:
            if self.is_appendable(token.column):
                #this is complex, yo can delete all this branch of the if and make it again
                last = self.stack[-1]
                if last.is_closable:
                    if last.is_match(token):
                        token_msg = f"Bad indentation for {token_repr(token)}."
                        token_msg += f"We expect {token.value} to be the end of a block started by {last.request_by}"
                        item_msg = f"Maybe you need {last.error_msg()}?"
                        poped_items.append(IndentErrorToken(token,last,token_msg, item_msg, None))
                        return poped_items
                else :
                    return poped_items

            last = self.stack.pop()

            if last.is_closable:
                if last.is_match(token):
                    if not self.is_valid_level(token.column):
                        token_msg = f"Bad indentation for {token_repr(token)}.\n"
                        token_msg += "Indentation must be greater than 0 always."
                        item_msg = f"Maybe you try to close block started by {last.error_msg()}?"
                        poped_items.append(IndentErrorToken(token,last,token_msg, item_msg, None))
                        return poped_items
                    if last.level==token.column:
                        poped_items.append(Dedent(last, token))
                        continue
                    else :
                        #token has lower indent than level
                        token_msg = f"Unexpected indentation for {token_repr(token)}."
                        item_msg += f"Maybe you forgot to close block started by {last.error_msg()}?"
                        poped_items.append(IndentErrorToken(token,last,token_msg, item_msg, None))
                        return poped_items

                else:
                    if not self.is_valid_level(token.column):
                        token_msg = f"Bad indentation for {token_repr(token)}."
                        token_msg += "\nIndentation must be greater than 0 always."
                        item_msg += f"Maybe you forgot to close block started by {last.error_msg()}?"
                        poped_items.append(IndentErrorToken(token,last,token_msg, item_msg, None))
                        return poped_items
                    else:
                        token_msg = f"Bad indentation for {token_repr(token)}."
                        token_msg += "\nIndentation must be greater than 0 always."
                        item_msg += f"Maybe you forgot to close block started by {last.error_msg()}?"
                        poped_items.append(IndentErrorToken(token,last,token_msg, item_msg, None))
                        return poped_items
                        
                

                    



         

