"Provides Indentation services for languages with indentation similar to Haskell"

from abc import ABC, abstractmethod
from typing import List, Iterator, Tuple, Dict, Optional
from enum import Enum, auto
import logging


from lark import logger
from lark.exceptions import LarkError
from lark.lark import PostLex
from lark.lexer import Token



class AtNextToken(Enum):
    add_block = auto()
    add_indent_start = auto()
    nothing = auto()

class IndentType(Enum):
    at_start = auto()
    at_end = auto()
    at_next = auto()

def show_token(token:Token):
    return f"{repr(token)} at line {token.line}, column {token.column}"

class IndenterError(Exception):
    token : Token
    pre_msg :str
    post_msg :str

class ExpectedCloseToken(IndenterError):
    item : "BlockStart"
    item_match_token : bool

    def __init__(self,token:Token, item:"BlockStart", item_match_token:bool,*args, **kwargs):
        self.token=token
        self.item=item
        self.item_match_token = item_match_token

        if item_match_token :
            self.pre_msg = f"Unexpected indentation for {show_token(self.token)}"
            self.post_msg = f"Must be indented at column {self.item.level} to close {show_token(self.item.token)}"
        else:
            self.pre_msg= f"Unexpected indentation for {show_token(self.token)}"
            self.post_msg=f"Waiting for indentation {item.level} according to {show_token(self.item.token)}"

        super().__init__(self.pre_msg+"\n"+self.post_msg,*args)

class IndentationAtZero(IndenterError):
    pass

class UnexpectedIndent(IndenterError):
    pass

class UnexpectedIndentBlock(UnexpectedIndent):
    last_token : Token
    item : "Indent"
    level :int

    def __init__(self, item:"Indent", level:int, token:Token, last_token:Token, *args, **kwargs):
        self.token=token
        self.item=item
        self.last_token = last_token
        self.level = level

        if isinstance(item, Indent):
            end = "."
        elif isinstance(item ,BlockStart):
            end = f"since block begin {show_token(item.token)}"
        self.pre_msg = f"Unexpected indentation for {show_token(token)}"
        self.post_msg = f"Expected indentation after {show_token(last_token)} must be {level}"+end

        super().__init__(self.pre_msg+"\n"+self.post_msg,*args)


class UnexpectedIndentRegular(UnexpectedIndent):
    last_token : Token
    token : Token
    item : "Indent"
    level :int

    def __init__(self, item:"Indent", level:int, token:Token, last_token:Optional[Token], *args, **kwargs):
        self.token=token
        self.item=item
        self.last_token = last_token
        self.level = level

        if isinstance(item, Indent):
            self.post_msg = f"it must be {level}"
        elif isinstance(item ,BlockStart):
            self.post_msg = f"it must align to {show_token(item.token)}."
        self.pre_msg = f"Unexpected indentation of {show_token(token)}"
        super().__init__(self.pre_msg+"\n"+self.post_msg,*args)

class ReportBug(IndenterError):
    pass


class Indentation():
    level : int
    def __init__(self, level:int)->None:
        self.level = level

class Indent(Indentation):
    def __repr__(self):
        return f"Indent(level={self.level})"

class BlockStart(Indentation):
    token_type:str
    end_type:str
    separator_type:str

    def __init__(self, token:Token, end_type:str, separator_type:str, level:int)->None:
        self.level = level
        self.token_type = token.type
        self.token = token
        self.end_type = end_type 
        self.separator_type = separator_type

    def match(self, token:Token)->bool:
        return self.end_type == token.type

    def make_separator(self, token:Token)->Token:
        return Token.new_borrow_pos(self.separator_type, "", token)

    def __repr__(self):
        return f"BlockStart(token={self.token_type}, end={self.end_type}, level={self.level}, separator={self.separator_type})"


class Indenter(PostLex, ABC):
    stack_state :List[Token]
    state: AtNextToken

    def __init__(self) -> None:
        self.stack_state = []
        self.state = AtNextToken.nothing
        self.indent_type, self.dedent_type, self.separator_type = self.REGULAR_INDENT
        self.produce_indent = self.PRODUCE_INDENT
        self.indent_blocks = self.INDENT_BLOCKS
        


    def make_separator(self,token:Token)->Token:
        return Token.new_borrow_pos(self.separator_type,"",token)

    def make_dedent(self,token:Token)->Token:
        return Token.new_borrow_pos(self.dedent_type,"",token)

    def make_indent(self,token:Token)->Token:
        return Token.new_borrow_pos(self.indent_type,"",token)

    def handle_token_indentation(self, token)->Iterator[Token]:
        """traverses stack until lower indentation is found or raises errors on bad states"""
        assert token.column>=0
        log = lambda x : logger.debug("handle_token_indentation "+x)
        log("begins")
        if len(self.stack_state)== 0 :
            log("no stack")
            return token 
        log2 = lambda x:log("loop "+x)
        log2("begins")
        while len(self.stack_state) != 0:
            item = self.stack_state[-1]
            log2(repr(item))

            if isinstance(item,Indent):
                log2("is Indent")
                if item.level == token.column :
                    yield self.make_separator(token)
                    break
                elif item.level > token.column :
                    yield self.make_dedent(token)
                    self.stack_state.pop()
                else:
                    break
            elif isinstance(item,BlockStart):
                log2("is BlockStart")
                if item.match(token):
                    log2("token match item")
                    if item.level <= token.column:
                        log2("same level, dedent")
                        self.stack_state.pop()
                        yield item.make_separator(token)
                        break
                    elif item.level > token.column:
                        log2("item>token, indent error")
                        raise ExpectedCloseToken(token, item, True)
                else:
                    log2("token wont close item")
                    if item.level > token.column:
                        log2("item>token, indentation error")
                        raise ExpectedCloseToken(token, item, False)
                    elif item.level == token.column:
                        log2("item==token, separator")
                        yield item.make_separator(token)
                        break
                    else:
                        log2("item<token, inline")
                        break
            else:
                raise ReportBug()

    def add_indent_token(self, level:int,token:Token,last_token:Optional[Token]=None)->None:
        if len(self.stack_state)>0:
            last_item = self.stack_state[-1]
            if last_item.level >= level:
                raise UnexpectedIndentRegular(last_item,level, token, last_token)
        item = Indent(level)
        self.stack_state.append(item)

    def add_indent_block(self, token:Token,last_token:Token)->None:
        if len(self.stack_state)>0:
            last_item = self.stack_state[-1]
            if last_item.level >= token.column:
                    raise UnexpectedIndentBlock(last_item, token.column , token, last_token)
        block = self.indent_blocks.get(last_token.type)
        if block is None :
            raise ReportBug()
        indent_place,end_type,separator_type = block
        if indent_place == IndentType.at_start:
            level = last_token.column
        elif indent_place == IndentType.at_end:
            level = last_token.column_end
        elif indent_place == IndentType.at_next:
            level = token.column
        else :
            raise ReportBug()
        block_item = BlockStart(last_token, end_type, separator_type, level)
        self.stack_state.append(block_item)

    def new_state(self, token:Token)->AtNextToken:
        """finds if indentation must be added to stack and returns state"""
        maybe_type = self.produce_indent.get(token.type)
        if maybe_type is None:
            maybe_block_tuple = self.indent_blocks.get(token.type)
            if maybe_block_tuple is None :
                return AtNextToken.nothing
            else :
                return AtNextToken.add_block
        else:
            if maybe_type == IndentType.at_start:
                self.add_indent_token(token.column, token)
                return AtNextToken.nothing
            elif maybe_type == IndentType.at_end:
                self.add_indent_token(token.column_end,token )
                return AtNextToken.nothing
            elif maybe_type == IndentType.at_next:
                return AtNextToken.add_indent_start
            else:
                raise ReportBug()

    def _process(self, stream:Iterator[Token])->Iterator[Token]:
        last_token = None
        for token in stream:
            logger.debug(f"_process begin state : {self.state} {self.stack_state}")
            if self.state == AtNextToken.add_block:
                logger.debug(f"_process add_block {repr(token)}")
                #we need to add the new token before match indentation or we loose info.
                if last_token is None :
                    raise ReportBug()

                self.add_indent_block(token,last_token)
                self.state = AtNextToken.nothing

            elif self.state == AtNextToken.add_indent_start:
                logger.debug(f"_process add indent {repr(token)}")
                if last_token is None :
                    raise ReportBug()

                self.add_indent_token(token.column, last_token)
                self.state = AtNextToken.nothing
            
            else:
                #there wasn't a pending order to add indentation at this token, so we only care of 
                #indentation stack
                logger.debug(f"_process nothing {repr(token)}")
                yield from self.handle_token_indentation(token) 

            
            self.state = self.new_state(token)
            last_token = token
            yield token




    def process(self, stream:Iterator[Token])->Iterator[Token]:
        self.stack_state = []
        return self._process(stream)

    # XXX Hack for ContextualLexer. Maybe there's a more elegant solution?
    @property
    def always_accept(self):
        return (self.REGULAR_INDENT[2],)

    @property
    @abstractmethod
    def INDENT_BLOCKS(self) -> Dict[str,Tuple[IndentType, str,str]]:
        """_BlockStart, _KindOfIndent, _BlockEnd, _ItemSeparator"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def PRODUCE_INDENT(self) -> Dict[str,IndentType]:
        """_Token, _KindOfIndent"""
        raise NotImplementedError()

    
    @property
    @abstractmethod
    def REGULAR_INDENT(self) -> Tuple[str, str,str]:
        """_Indent, _Dedent, _NL"""
        raise NotImplementedError()
