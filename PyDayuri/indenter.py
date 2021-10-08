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
            self.post_msg = f"Indentation must be at {self.item.token.column} or greater to close {show_token(self.item.token)}"
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

    def make_separator(self, token:Token, level:Optional[int]=None)->Token:
        return self.make_with_level(token, level)

    def make_with_level(self,token:Token, level:Optional[int]=None)->Token:
        if level :
            tok = Token(self.separator_type, "")
            tok.column = level
            tok.end_column = level
            tok.line = token
            tok.end_line = token
            # we don't know this and can't just borrow token as token position could
            #be behind level (but not further)
            #tok.start_pos = -1
            #tok.end_pos = -1
            return tok
        return Token.new_borrow_pos(self.separator_type,"",token)

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
        

    def make_with_level(self,token:Token, _type:str, level:Optional[int]=None)->Token:
        if level :
            tok = Token(_type, "")
            tok.column = level
            tok.end_column = level
            tok.line = token
            tok.end_line = token
            # we don't know this and can't just borrow token as token position could
            #be behind level (but not further)
            #tok.start_pos = -1
            #tok.end_pos = -1
            return tok
        return Token.new_borrow_pos(_type,"",token)

    def make_separator(self,token:Token, level:Optional[int]=None)->Token:
        return self.make_with_level(token, self.separator_type, level)

    def make_dedent(self,token:Token, level:Optional[int]=None)->Token:
        return self.make_with_level(token, self.dedent_type, level)

    def make_indent(self,token:Token, level:Optional[int]=None)->Token:
        return self.make_with_level(token, self.indent_type, level)

    def handle_token_indentation(self, token)->Iterator[Token]:
        """traverses stack until lower indentation is found or raises errors on bad states"""
        assert token.column>=0
        if len(self.stack_state)== 0 :
            logb("stack is empty, accepting token")
            return token 

        logb("loop start")
        while len(self.stack_state) != 0:
            item = self.stack_state[-1]
            logb(f"top item={repr(item)}")

            if isinstance(item,Indent):
                if item.level == token.column :
                    logb("token is at level of stack item, injecting separator")
                    yield self.make_separator(token)
                    break
                elif item.level > token.column :
                    logb("stack item is further indented than token, inject dedent and pop item")
                    yield self.make_dedent(token)
                    self.stack_state.pop()
                else:
                    logb("token is further indented than stack item, inlining token")
                    break
            elif isinstance(item,BlockStart):
                if item.match(token):
                    logb(f"{repr(item)} is closed by {show_token(token)}")
                    #if item.token.column.level <= token.column:
                    if item.token.column <= token.column:
                        logb("token is further indented than stack item, poping item")
                        #we could inject a separator before end, but we choose to don't
                        #yield item.make_separator(token)
                        self.stack_state.pop()
                        break
                    elif item.level > token.column:
                        logb("stack item is further indented than token, bad indent for closing item")
                        raise ExpectedCloseToken(token, item, True)
                else:
                    logb("token won't close item")
                    if item.level > token.column:
                        logb("stack item is further indented than token, indentation error or missing close token")
                        raise ExpectedCloseToken(token, item, False)
                    elif item.level == token.column:
                        logb("token is at same level of stack item, injecting separator ")
                        yield item.make_separator(token)
                        break
                    else:
                        logb("token further indented than stack item, inlining token")
                        break
            else:
                raise ReportBug()

    def check_level(self, level:int, current_stream_token: Token,token_that_trigger_add:Token)->None:
        would_rise = False
        if level< token_that_trigger_add.column:
            would_rise = True
            pre_msg = f"Unexpected indent for {show_token(current_stream_token)}"
            post_msg = f"Indent must be greater or equal than {show_token(token_that_trigger_add)}"
        if level == token_that_trigger_add.column:
            if level == token_that_trigger_add.end_column:
                if level < current_stream_token.column:
                    #this is supposed to be handled by first indent
                    would_rise = True
                    pre_msg = f"Unexpected indent for {show_token(current_stream_token)}"
                    post_msg = "Indent must be greater or equal than {level} as requested by {show_token(token_that_trigger_add)}"
            elif level < current_stream_token.column:
                would_rise = True
                pre_msg = f"Unexpected indent for {show_token(current_stream_token)}"
                post_msg = f"Indent must be greater or equal than {level} as requested by {show_token(token_that_trigger_add)}"
        elif level == token_that_trigger_add.end_column:
            if level < current_stream_token.column:
                would_rise = True
                pre_msg = f"Unexpected indent for {show_token(current_stream_token)}"
                post_msg = f"Indent must be greater or equal than {level} as requested by {show_token(token_that_trigger_add)}"
        elif level< token_that_trigger_add.end_column :
            would_rise = True
            pre_msg = f"Unexpected indent for {show_token(current_stream_token)}"
            post_msg = f"Indent must be strictly greater than {token_that_trigger_add.end_column} since we have {show_token(token_that_trigger_add)}"

        if would_rise:
            exception = UnexpectedIndent()
            exception.pre_msg = pre_msg
            exception.post_msg = post_msg
            exception.token = current_stream_token
            raise exception


    def add_indent_token(self, level:int, current_stream_token: Token,token_that_trigger_add:Token)->List[Token]:
        logb(f"got : {level}, {show_token(current_stream_token)}, {show_token(token_that_trigger_add)}")
        if len(self.stack_state)>0:
            last_item = self.stack_state[-1]
            logb("stack isn't empty, check if token is indented further")
            if last_item.level >= level:
                logb("new indent level is too short")
                raise UnexpectedIndentRegular(last_item,level, current_stream_token, token_that_trigger_add)
        else : 
            if level<=0:
                raise IndentationAtZero()

        logb(f"{level}, {show_token(current_stream_token)}")

        self.check_level(level, current_stream_token, token_that_trigger_add)

        item = Indent(level)
        logb("adding Indent to stack")
        self.stack_state.append(item)
        logb(f"injecting anon indent for {show_token(current_stream_token)} with level={level}, injection separator")
        return [self.make_indent(current_stream_token, level), self.make_separator(current_stream_token, level)]

    def add_indent_block(self, token:Token,last_token:Token)->List[Token]:
        if len(self.stack_state)>0:
            last_item = self.stack_state[-1]
            logb("stack isn't empty, check if token is indented further")
            if last_item.level >= token.column:
                logb("new indent level is too short")
                raise UnexpectedIndentBlock(last_item, token.column , token, last_token)
        else : 
            if token.column<=0:
                raise IndentationAtZero()

        block = self.indent_blocks.get(last_token.type)
        if block is None :
            logb("we had tested before that last_token is part of named block producers, this only makes sense on bug")
            raise ReportBug()
        indent_place,end_type,separator_type = block
        logb(f"named block info: indent={indent_place}, ends_at={end_type}, produce_separators={separator_type}")
        if indent_place == IndentType.at_start:
            logb(f"set level at start of {show_token(last_token)}")
            level = last_token.column
        elif indent_place == IndentType.at_end:
            logb(f"set level at end of {show_token(last_token)}")
            level = last_token.column_end
        elif indent_place == IndentType.at_next:
            logb(f"set level at start of {show_token(token)}")
            level = token.column
        else :
            logb("We expect indent_place to be a IndentType and had just this cases")
            raise ReportBug()

        self.check_level(level, token, last_token)

        block_item = BlockStart(last_token, end_type, separator_type, level)
        logb("adding BlockStart to stack")
        self.stack_state.append(block_item)
        logb(f"injecting separator at {token}")
        return [block_item.make_separator(token)]

    def process_indentation_start(self, token:Token)->Tuple[AtNextToken, List[Token]]:
        """finds if indentation must be added to stack and returns state"""
        logb("testing if token is an anon block producer")
        maybe_type = self.produce_indent.get(token.type)
        if maybe_type is None:
            logb("testing if token is a named block producer")
            maybe_block_tuple = self.indent_blocks.get(token.type)
            if maybe_block_tuple is None :
                logb("token wasn't a block producer")
                return (AtNextToken.nothing, [])
            else :
                logb("set state to add named block at next token")
                return (AtNextToken.add_block,[])
        else:
            if maybe_type == IndentType.at_start:
                logb("adding anon block at token start={token.column}")
                out_tokens = self.add_indent_token(token.column, token, token)
                return (AtNextToken.nothing, out_tokens)
            elif maybe_type == IndentType.at_end:
                logb("adding anon block at token end={token.column_end}")
                out_tokens = self.add_indent_token(token.column_end,token, token )
                return (AtNextToken.nothing, out_tokens)
            elif maybe_type == IndentType.at_next:
                logb("set state to add anon block at next token")
                return (AtNextToken.add_indent_start, [])
            else:
                raise ReportBug()

    def _process(self, stream:Iterator[Token])->Iterator[Token]:
        last_token = None
        for token in stream:
            logb(f"for begins with {show_token(token)}")
            logb(f"state : {repr(self)}")
            if self.state == AtNextToken.add_block:
                #we need to add the new token before match indentation or we loose info.
                if last_token is None :
                    raise ReportBug()

                logb(f"adding block started by {show_token(last_token)}, at level of {show_token(token)}")
                to_inject= self.add_indent_block(token,last_token)
                for tok in to_inject:
                    logb(f"yield inyected token {tok}")
                    yield tok
                logb("state set to nothing")
                self.state = AtNextToken.nothing

            elif self.state == AtNextToken.add_indent_start:
                if last_token is None :
                    raise ReportBug()

                logb(f"adding anon block started by {show_token(last_token)}, at level of {show_token(token)}")
                to_inject = self.add_indent_token(token.column, token, last_token)
                for tok in to_inject:
                    logb(f"yield inyected token {show_token(tok)}")
                    yield tok
                logb("state set to nothing")
                self.state = AtNextToken.nothing
            
            else:
                #there wasn't a pending order to add indentation at this token, so we only care of 
                #indentation stack
                logb(f"checking if we need to dedent {show_token(token)}")
                yield from self.handle_token_indentation(token) 

            
            logb("pending emits of new blocks or dedents were handled")
            logb("testing if we need to inject tokens or set state")
            self.state,inject = self.process_indentation_start(token)
            if len(inject ) ==0:
                logb("Nothing to inject")
            else :
                for tok in inject:
                    logb(f"yielding {show_token(tok)}")
                    yield tok
            last_token = token
            yield token

        logb(f"reached EOF handling end state : {repr(self)}")
        while len (self.stack_state) !=0:
            item = self.stack_state.pop()
            logb(f"handling {repr(item)}")
            if isinstance(item, Indent):
                logb("yield inject dedent")
                yield self.make_dedent(token, token.end_column)
            elif isinstance(item, BlockStart):
                logb("Missing at least {item.end_type} to close this block")
                end_token = self.make_with_level(token, token.end_column)
                end_token.type = "$END"
                raise ExpectedCloseToken(end_token, item, False)
            else:
                raise ReportBug()



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

    def __repr__(self):
        state = str(self.state)
        if len(self.stack_state)==0 :
            return state + " [ ]"
        stack = [repr(item)  for item in self.stack_state]
        stack_str = ",\n    ".join(stack)
        return state + "\n    [    \n    " + stack_str + "\n    ]"

