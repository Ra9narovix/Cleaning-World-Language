import sys
import os
import re
from ast_nodes import *

class Token:
    def __init__(self, line, tid, kind, lexeme):
        self.line = int(line)
        self.tid = int(tid)
        self.kind = kind.strip()
        self.lexeme = lexeme.strip()
    
    def __str__(self):
        return f"[{self.kind}] '{self.lexeme}'"
    
    def __repr__(self):
        return self.__str__()

class Parser:
    def __init__(self, token_objects):
        self.tokens = token_objects
        self.current_token_index = 0
        self.current_token = self.tokens[0] if self.tokens else None

    def parse(self):
        """Entry point: Returns the Root CST Node."""
        if not self.tokens: return None
        try:
            cst = self._parse_program()
            if self.current_token and self.current_token_index < len(self.tokens):
                raise SyntaxError(f"Line {self.current_token.line}: Unexpected token '{self.current_token.lexeme}' after program completion.")
            print("[INFO] Syntax Analysis (CST Generation): SUCCESS")
            return cst
        except SyntaxError as e:
            print(f"[SYNTAX ERROR] {e}")
            return None
        except Exception as e:
            print(f"[FATAL PARSER ERROR] {e}")
            return None

    def _next_token(self):
        self.current_token_index += 1
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
        else:
            self.current_token = None 

    def _expect(self, kind, lexeme=None):
        if not self.current_token:
            raise SyntaxError(f"Unexpected End of File. Expected token '{kind}'.")
        if self.current_token.kind == kind and (lexeme is None or self.current_token.lexeme == lexeme):
            token = self.current_token
            self._next_token()
            return token
        else:
            expected = f"Kind: '{kind}'"
            if lexeme is not None: expected += f", Lexeme: '{lexeme}'"
            raise SyntaxError(f"Line {self.current_token.line}: Expected {expected}, got K:'{self.current_token.kind}', L:'{self.current_token.lexeme}'")

    def _peek(self, kind=None, lexeme=None):
        if not self.current_token: return False
        if kind and self.current_token.kind != kind: return False
        if lexeme and self.current_token.lexeme != lexeme: return False
        return True

    def _parse_program(self):
        node = CSTNode("program")
        node.add_child(self._expect('PROGRAM'))
        node.add_child(self._expect('ID'))
        node.add_child(self._expect('BEGIN'))
        
        node.add_child(self._parse_top_items())
        node.add_child(self._parse_main_decl())
        
        node.add_child(self._expect('END'))
        if self._peek('END'): node.add_child(self._expect('END'))
        return node

    def _parse_top_items(self):
        node = CSTNode("top_items")
        while self._peek('VAR') or self._peek('FUNC'):
            if self._peek('VAR'):
                node.add_child(self._parse_var_decl())
            elif self._peek('FUNC'):
                next_idx = self.current_token_index + 1
                is_main = False
                if next_idx < len(self.tokens):
                    if self.tokens[next_idx].lexeme == 'main': is_main = True
                
                if is_main: break
                else: node.add_child(self._parse_func_decl())
            else: break
        return node

    def _parse_main_decl(self):
        node = CSTNode("main_decl")
        node.add_child(self._expect('FUNC'))
        node.add_child(self._expect('ID', 'main'))
        node.add_child(self._expect('LPAREN'))
        node.add_child(self._expect('RPAREN'))
        node.add_child(self._expect('BEGIN'))
        node.add_child(self._parse_stmt_list())
        node.add_child(self._expect('END'))
        return node

    def _parse_var_decl(self):
        node = CSTNode("var_decl")
        node.add_child(self._expect('VAR'))
        node.add_child(self._parse_id_list())
        node.add_child(self._expect('SEMI'))
        return node

    def _parse_id_list(self):
        node = CSTNode("id_list")
        node.add_child(self._expect('ID'))
        while self._peek('COMMA'):
            node.add_child(self._expect('COMMA'))
            node.add_child(self._expect('ID'))
        return node

    def _parse_func_decl(self):
        node = CSTNode("func_decl")
        node.add_child(self._expect('FUNC'))
        node.add_child(self._expect('ID'))
        node.add_child(self._expect('LPAREN'))
        if not self._peek('RPAREN'):
            node.add_child(self._parse_params())
        node.add_child(self._expect('RPAREN'))
        
        if self._peek('COLON'):
            node.add_child(self._expect('COLON'))
            node.add_child(self._expect('TYPE'))
            
        node.add_child(self._expect('BEGIN'))
        node.add_child(self._parse_stmt_list())
        node.add_child(self._expect('END'))
        return node

    def _parse_params(self):
        node = CSTNode("params")
        node.add_child(self._parse_param())
        while self._peek('COMMA'):
            node.add_child(self._expect('COMMA'))
            node.add_child(self._parse_param())
        return node

    def _parse_param(self):
        node = CSTNode("param")
        node.add_child(self._expect('ID'))
        node.add_child(self._expect('COLON'))
        node.add_child(self._expect('TYPE'))
        return node

    def _parse_stmt_list(self):
        node = CSTNode("stmt_list")
        while (self._peek('ID') or self._peek('PRINT') or self._peek('IF') or 
               self._peek('WHILE') or self._peek('BREAK') or self._peek('RETURN') or
               self._peek('WORLD') or self._peek('AGENT')):
            node.add_child(self._parse_stmt())
        return node

    def _parse_stmt(self):
        node = CSTNode("stmt")
        if self._peek('PRINT'): 
            node.add_child(self._parse_print_stmt())
            return node
        if self._peek('IF'):
            node.add_child(self._parse_if_stmt())
            return node
        if self._peek('WHILE'):
            node.add_child(self._parse_while_stmt())
            return node
        if self._peek('BREAK'):
            node.add_child(self._parse_break_stmt())
            return node
        if self._peek('RETURN'):
            node.add_child(self._parse_return_stmt())
            return node
        if self._peek('WORLD') or self._peek('AGENT'):
            node.add_child(self._parse_assign_stmt())
            return node
        if self._peek('ID'):
            next_token = self.tokens[self.current_token_index + 1] if self.current_token_index + 1 < len(self.tokens) else None
            if next_token and next_token.kind == 'ASSIGN':
                node.add_child(self._parse_assign_stmt())
            elif next_token and next_token.kind == 'LPAREN':
                node.add_child(self._parse_call_stmt())
            else:
                raise SyntaxError(f"Line {self.current_token.line}: Invalid statement.")
            return node
        raise SyntaxError(f"Line {self.current_token.line}: Invalid statement.")

    def _parse_assign_stmt(self):
        node = CSTNode("assign_stmt")
        if self._peek('WORLD'): node.add_child(self._expect('WORLD'))
        elif self._peek('AGENT'): node.add_child(self._expect('AGENT'))
        else: node.add_child(self._expect('ID'))
        
        node.add_child(self._expect('ASSIGN'))
        node.add_child(self._parse_expr())
        node.add_child(self._expect('SEMI'))
        return node

    def _parse_call_stmt(self):
        node = CSTNode("call_stmt")
        node.add_child(self._expect('ID'))
        node.add_child(self._expect('LPAREN'))
        if not self._peek('RPAREN'):
            node.add_child(self._parse_args())
        node.add_child(self._expect('RPAREN'))
        node.add_child(self._expect('SEMI'))
        return node

    def _parse_print_stmt(self):
        node = CSTNode("print_stmt")
        node.add_child(self._expect('PRINT'))
        node.add_child(self._expect('LPAREN'))
        node.add_child(self._parse_expr())
        node.add_child(self._expect('RPAREN'))
        node.add_child(self._expect('SEMI'))
        return node

    def _parse_if_stmt(self):
        node = CSTNode("if_stmt")
        node.add_child(self._expect('IF'))
        node.add_child(self._parse_expr())
        node.add_child(self._expect('THEN'))
        node.add_child(self._parse_stmt_list())
        
        if self._peek('ELSE'):
            node.add_child(self._expect('ELSE'))
            if self._peek('IF'):
                node.add_child(self._parse_if_stmt())
                return node 
            else:
                node.add_child(self._parse_stmt_list())
                
        node.add_child(self._expect('END'))
        return node

    def _parse_while_stmt(self):
        node = CSTNode("while_stmt")
        node.add_child(self._expect('WHILE'))
        node.add_child(self._parse_expr())
        node.add_child(self._expect('DO'))
        node.add_child(self._parse_stmt_list())
        node.add_child(self._expect('END'))
        return node

    def _parse_break_stmt(self):
        node = CSTNode("break_stmt")
        node.add_child(self._expect('BREAK'))
        node.add_child(self._expect('SEMI'))
        return node

    def _parse_return_stmt(self):
        node = CSTNode("return_stmt")
        node.add_child(self._expect('RETURN'))
        if not self._peek('SEMI'):
            node.add_child(self._parse_expr())
        node.add_child(self._expect('SEMI'))
        return node

    def _parse_args(self):
        node = CSTNode("args")
        node.add_child(self._parse_expr())
        while self._peek('COMMA'):
            node.add_child(self._expect('COMMA'))
            node.add_child(self._parse_expr())
        return node

    def _parse_expr(self):
        node = CSTNode("expr")
        node.add_child(self._parse_or_expr())
        return node

    def _parse_or_expr(self):
        node = CSTNode("or_expr")
        node.add_child(self._parse_and_expr())
        while self._peek('OR'):
            node.add_child(self._expect('OR'))
            node.add_child(self._parse_and_expr())
        return node

    def _parse_and_expr(self):
        node = CSTNode("and_expr")
        node.add_child(self._parse_rel_expr())
        while self._peek('AND'):
            node.add_child(self._expect('AND'))
            node.add_child(self._parse_rel_expr())
        return node

    def _parse_rel_expr(self):
        node = CSTNode("rel_expr")
        node.add_child(self._parse_add_expr())
        if self._peek('EQ') or self._peek('NEQ') or self._peek('LT') or self._peek('LE') or self._peek('GT') or self._peek('GE'):
            node.add_child(self.current_token) 
            self._next_token()
            node.add_child(self._parse_add_expr())
        return node

    def _parse_add_expr(self):
        node = CSTNode("add_expr")
        node.add_child(self._parse_mul_expr())
        while self._peek('PLUS') or self._peek('MINUS'):
            node.add_child(self.current_token)
            self._next_token()
            node.add_child(self._parse_mul_expr())
        return node

    def _parse_mul_expr(self):
        node = CSTNode("mul_expr")
        node.add_child(self._parse_unary())
        while self._peek('STAR') or self._peek('SLASH'):
            node.add_child(self.current_token)
            self._next_token()
            node.add_child(self._parse_unary())
        return node

    def _parse_unary(self):
        node = CSTNode("unary")
        if self._peek('NOT'):
            node.add_child(self._expect('NOT'))
            node.add_child(self._parse_unary())
        else:
            node.add_child(self._parse_primary())
        return node

    def _parse_primary(self):
        node = CSTNode("primary")
        if self._peek('LPAREN'):
            node.add_child(self._expect('LPAREN'))
            node.add_child(self._parse_expr())
            node.add_child(self._expect('RPAREN'))
        elif self._peek('ID'):
            next_idx = self.current_token_index + 1
            is_call = False
            if next_idx < len(self.tokens) and self.tokens[next_idx].kind == 'LPAREN':
                is_call = True
            
            if is_call:
                node.add_child(self._expect('ID'))
                node.add_child(self._expect('LPAREN'))
                if not self._peek('RPAREN'):
                    node.add_child(self._parse_args())
                node.add_child(self._expect('RPAREN'))
            else:
                node.add_child(self._expect('ID'))
        else:
            token = self.current_token
            if token.kind in ['INT', 'STR', 'BOOL', 'DIR', 'WORLD', 'AGENT']:
                node.add_child(token)
                self._next_token()
            else:
                raise SyntaxError(f"Unexpected token {token.lexeme}")
        return node

class CSTtoAST:
    def __init__(self):
        self.in_loop = 0 

    def build_program(self, cst):
        name_token = cst.children[1] 
        top_items_cst = cst.children[3]
        main_decl_cst = cst.children[4]

        declarations = self.build_top_items(top_items_cst)
        main_func = self.build_main_decl(main_decl_cst)
        
        return Program(name_token, declarations, main_func)

    def build_top_items(self, cst):
        decls = []
        for child in cst.children:
            if isinstance(child, CSTNode):
                if child.name == "var_decl":
                    decls.append(self.build_var_decl(child))
                elif child.name == "func_decl":
                    decls.append(self.build_func_decl(child))
        return decls

    def build_var_decl(self, cst):
        id_list_cst = cst.children[1]
        ids = []
        for child in id_list_cst.children:
            if isinstance(child, Token) and child.kind == 'ID':
                ids.append(child)
        return VarDecl(ids, cst.children[0])

    def build_main_decl(self, cst):
        stmt_list_cst = cst.children[5]
        stmts = self.build_stmt_list(stmt_list_cst)
        return FuncDecl(cst.children[1], [], 'void', stmts, cst.children[0])

    def build_func_decl(self, cst):
        name = cst.children[1]
        params = []
        return_type = 'void'
        
        idx = 3
        if isinstance(cst.children[3], CSTNode) and cst.children[3].name == "params":
            params = self.build_params(cst.children[3])
            idx = 4 
        
        idx += 1 
        
        if idx < len(cst.children) and isinstance(cst.children[idx], Token) and cst.children[idx].kind == 'COLON':
            return_type = cst.children[idx+1].lexeme
            idx += 2
        
        stmt_list_cst = cst.children[idx+1]
        body = self.build_stmt_list(stmt_list_cst)
        
        return FuncDecl(name, params, return_type, body, cst.children[0])

    def build_params(self, cst):
        params = []
        for child in cst.children:
            if isinstance(child, CSTNode) and child.name == "param":
                p_name = child.children[0]
                p_type = child.children[2]
                params.append(Param(p_name, p_type))
        return params

    def build_stmt_list(self, cst):
        sl = StmtList()
        for child in cst.children:
            if isinstance(child, CSTNode) and child.name == "stmt":
                sl.add_child(self.build_stmt(child.children[0]))
        return sl

    def build_stmt(self, cst):
        kind = cst.name
        if kind == "print_stmt": return self.build_print(cst)
        if kind == "assign_stmt": return self.build_assign(cst)
        if kind == "call_stmt": return self.build_call(cst)
        if kind == "if_stmt": return self.build_if(cst)
        if kind == "while_stmt": return self.build_while(cst)
        if kind == "break_stmt": return BreakStmt(cst.children[0])
        if kind == "return_stmt": return self.build_return(cst)
        return None

    def build_print(self, cst):
        expr = self.build_expr(cst.children[2])
        return PrintStmt(expr, cst.children[0])

    def build_assign(self, cst):
        target_tok = cst.children[0]
        expr = self.build_expr(cst.children[2])
        
        target_node = Identifier(target_tok)
        if target_tok.kind == 'WORLD': target_node = WorldObject(target_tok)
        if target_tok.kind == 'AGENT': target_node = AgentObject(target_tok)
        
        return AssignStmt(target_node, expr, cst.children[1])

    def build_call(self, cst):
        name = cst.children[0]
        args = []
        if isinstance(cst.children[2], CSTNode) and cst.children[2].name == "args":
            args = self.build_args(cst.children[2])
        return CallStmt(name, args, name)

    def build_args(self, cst):
        args = []
        for child in cst.children:
            if isinstance(child, CSTNode) and child.name == "expr":
                args.append(self.build_expr(child))
        return args

    def build_if(self, cst):
        condition = self.build_expr(cst.children[1])
        then_block = self.build_stmt_list(cst.children[3])
        else_block = None
        
        if len(cst.children) > 4 and isinstance(cst.children[4], Token) and cst.children[4].kind == 'ELSE':
            else_content = cst.children[5]
            if else_content.name == "if_stmt":
                nested_if_ast = self.build_if(else_content)
                else_block = StmtList()
                else_block.add_child(nested_if_ast)
            else:
                else_block = self.build_stmt_list(else_content)
                
        return IfStmt(condition, then_block, else_block, cst.children[0])

    def build_while(self, cst):
        cond = self.build_expr(cst.children[1])
        body = self.build_stmt_list(cst.children[3])
        return WhileStmt(cond, body, cst.children[0])

    def build_return(self, cst):
        expr = None
        if len(cst.children) > 2: 
            expr = self.build_expr(cst.children[1])
        return ReturnStmt(expr, cst.children[0])

    def build_expr(self, cst):
        return self.build_or_expr(cst.children[0])

    def build_or_expr(self, cst):
        left = self.build_and_expr(cst.children[0])
        i = 1
        while i < len(cst.children):
            op = cst.children[i] 
            right = self.build_and_expr(cst.children[i+1])
            left = BinaryOp(op, left, right)
            i += 2
        return left

    def build_and_expr(self, cst):
        left = self.build_rel_expr(cst.children[0])
        i = 1
        while i < len(cst.children):
            op = cst.children[i]
            right = self.build_rel_expr(cst.children[i+1])
            left = BinaryOp(op, left, right)
            i += 2
        return left

    def build_rel_expr(self, cst):
        left = self.build_add_expr(cst.children[0])
        if len(cst.children) > 1:
            op = cst.children[1]
            right = self.build_add_expr(cst.children[2])
            return BinaryOp(op, left, right)
        return left

    def build_add_expr(self, cst):
        left = self.build_mul_expr(cst.children[0])
        i = 1
        while i < len(cst.children):
            op = cst.children[i]
            right = self.build_mul_expr(cst.children[i+1])
            left = BinaryOp(op, left, right)
            i += 2
        return left

    def build_mul_expr(self, cst):
        left = self.build_unary(cst.children[0])
        i = 1
        while i < len(cst.children):
            op = cst.children[i]
            right = self.build_unary(cst.children[i+1])
            left = BinaryOp(op, left, right)
            i += 2
        return left

    def build_unary(self, cst):
        first = cst.children[0]
        if isinstance(first, Token) and first.kind == 'NOT':
            expr = self.build_unary(cst.children[1])
            return UnaryOp(first, expr)
        else:
            return self.build_primary(first)

    def build_primary(self, cst):
        first = cst.children[0]
        if isinstance(first, Token):
            if first.kind in ['INT', 'STR', 'BOOL', 'DIR']: return Literal(first)
            if first.kind == 'WORLD': return WorldObject(first)
            if first.kind == 'AGENT': return AgentObject(first)
            if first.kind == 'LPAREN': return self.build_expr(cst.children[1]) 
            if first.kind == 'ID':
                if len(cst.children) > 1: 
                    name = first
                    args = []
                    if len(cst.children) > 3: 
                         args = self.build_args(cst.children[2])
                    return FuncCallExpr(name, args, name)
                else:
                    return Identifier(first)
        return None 

BUILTIN_TYPES = {'int', 'bool', 'string', 'world', 'agent', 'dir'}
BUILTIN_FUNCTIONS = {
    'init_world': ('world', ['int', 'int']),
    'set_agent': ('agent', ['world', 'int', 'int', 'dir']),
    'dirt_remaining': ('int', ['world']),
    'is_dirty': ('bool', ['agent']),
    'clean': ('void', ['agent']),
    'move_forward': ('void', ['agent']),
    'turn_right': ('void', ['agent']),
    'front_is_blocked': ('bool', ['agent']),
    'print': ('void', ['any']),
}

class SymbolTable:
    def __init__(self, parent=None):
        self.table = {}
        self.parent = parent 
    def enter_scope(self): return SymbolTable(parent=self)
    def exit_scope(self): return self.parent
    def add_symbol(self, name, kind, data_type, token):
        if name in self.table: raise SemanticError(f"Redeclaration of '{name}' on line {token.line}")
        self.table[name] = {'kind': kind, 'type': data_type, 'token': token}
    def lookup(self, name):
        scope = self
        while scope:
            if name in scope.table: return scope.table[name]
            scope = scope.parent
        return None

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self._initialize_builtins()
        self.current_function_return_type = None

    def _initialize_builtins(self):
        self.symbol_table.add_symbol('world', 'object', 'world', Token(0, 30, 'WORLD', 'world'))
        self.symbol_table.add_symbol('agent', 'object', 'agent', Token(0, 31, 'AGENT', 'agent'))

    def check_program(self, ast):
        try:
            for decl in ast.declarations:
                if isinstance(decl, VarDecl): self.check_var_decl(decl)
                elif isinstance(decl, FuncDecl): self.register_func_decl(decl)
            self.check_func_decl(ast.main_func)
            print("\n[INFO] Static Semantics Check: SUCCESS")
            return True
        except SemanticError as e:
            print(f"\n[SEMANTIC ERROR] {e}")
            return False

    def check_var_decl(self, node):
        var_type = 'int' 
        for id_token in node.id_list: self.symbol_table.add_symbol(id_token.lexeme.lower(), 'variable', var_type, id_token)

    def register_func_decl(self, node):
        params_types = [p.type for p in node.params]
        return_type = node.return_type or 'void'
        if node.name.lexeme in BUILTIN_FUNCTIONS: raise SemanticError(f"Cannot redefine built-in '{node.name.lexeme}'")
        self.symbol_table.add_symbol(node.name.lexeme, 'function', {'return': return_type, 'params': params_types}, node.name)

    def check_func_decl(self, node):
        self.symbol_table = self.symbol_table.enter_scope()
        self.current_function_return_type = node.return_type or 'void'
        for param in node.params: self.symbol_table.add_symbol(param.name.lexeme.lower(), 'parameter', param.type, param.name)
        self.check_stmt_list(node.body)
        self.symbol_table = self.symbol_table.exit_scope()
        self.current_function_return_type = None

    def check_stmt_list(self, node):
        for stmt in node.children: self.check_stmt(stmt)

    def check_stmt(self, node):
        if isinstance(node, AssignStmt): self._check_assign_stmt(node)
        elif isinstance(node, CallStmt): self._check_call_stmt(node, is_expr=False)
        elif isinstance(node, PrintStmt): self._check_print_stmt(node)
        elif isinstance(node, IfStmt): self._check_if_stmt(node)
        elif isinstance(node, WhileStmt): self._check_while_stmt(node)
        elif isinstance(node, ReturnStmt): self._check_return_stmt(node)
        elif isinstance(node, Identifier): pass 
        elif isinstance(node, BreakStmt): pass
        
    def _check_assign_stmt(self, node):
        # Normalize identifier name to lowercase for lookup (WORLD/AGENT tokens have lowercase lexemes)
        target_name = node.target.lexeme.lower()
        symbol = self.symbol_table.lookup(target_name)
        if not symbol: raise SemanticError(f"Undeclared identifier '{node.target.lexeme}' line {node.target.token.line}")
        if symbol['kind'] not in ['variable', 'parameter', 'object']: raise SemanticError(f"Cannot assign to '{node.target.lexeme}'")
        expr_type = self._check_expr(node.expr)
        node.expr.type = expr_type
        node.type = expr_type 
        
    def _check_call_stmt(self, node, is_expr):
        func_name = node.name.lexeme
        if func_name in BUILTIN_FUNCTIONS:
            expected_return, expected_params = BUILTIN_FUNCTIONS[func_name]
            if is_expr and expected_return == 'void': raise SemanticError(f"Procedure '{func_name}' used in expression")
            if len(node.args) != len(expected_params): raise SemanticError(f"'{func_name}' expects {len(expected_params)} args, got {len(node.args)}")
            for i, (arg, expected_type) in enumerate(zip(node.args, expected_params)):
                arg_type = self._check_expr(arg)
                arg.type = arg_type
                # Special handling for 'any' type (used by print)
                if expected_type == 'any':
                    # Allow any printable type
                    if arg_type not in BUILTIN_TYPES and arg_type != 'dir': 
                        raise SemanticError(f"Arg {i+1} of '{func_name}' must be a printable type (int, bool, string, dir), got {arg_type}")
                elif expected_type == 'dir' and arg.token.kind != 'DIR': 
                    raise SemanticError(f"Arg {i+1} of '{func_name}' must be Direction")
                elif expected_type in BUILTIN_TYPES and arg_type != expected_type: 
                    raise SemanticError(f"Arg {i+1} of '{func_name}' expects {expected_type}, got {arg_type}")
            node.type = expected_return
            return expected_return

        symbol = self.symbol_table.lookup(func_name)
        if not symbol or symbol['kind'] != 'function': raise SemanticError(f"Undeclared function '{func_name}'")
        func_data = symbol['type']
        if is_expr and func_data['return'] == 'void': raise SemanticError(f"Procedure '{func_name}' used in expression")
        if len(node.args) != len(func_data['params']): raise SemanticError(f"'{func_name}' expects {len(func_data['params'])} args")
        for i, (arg, expected_type) in enumerate(zip(node.args, func_data['params'])):
            arg_type = self._check_expr(arg)
            if arg_type != expected_type: raise SemanticError(f"Arg {i+1} of '{func_name}' expects {expected_type}")
        node.type = func_data['return']
        return func_data['return']

    def _check_print_stmt(self, node):
        expr_type = self._check_expr(node.expr)
        if expr_type not in BUILTIN_TYPES and expr_type != 'dir': raise SemanticError(f"Cannot print type '{expr_type}'")

    def _check_if_stmt(self, node):
        if self._check_expr(node.condition) != 'bool': raise SemanticError("If condition must be bool")
        self.check_stmt_list(node.then_block)
        if node.else_block: self.check_stmt_list(node.else_block)

    def _check_while_stmt(self, node):
        if self._check_expr(node.condition) != 'bool': raise SemanticError("While condition must be bool")
        self.check_stmt_list(node.body)

    def _check_return_stmt(self, node):
        if self.current_function_return_type == 'void':
            if node.expr: raise SemanticError("Void function cannot return value")
        else:
            if not node.expr: raise SemanticError(f"Function must return {self.current_function_return_type}")
            if self._check_expr(node.expr) != self.current_function_return_type: raise SemanticError(f"Return type mismatch")

    def _check_expr(self, node):
        if isinstance(node, Literal): return node.type 
        if isinstance(node, Identifier):
            # Normalize to lowercase for lookup consistency
            name = node.lexeme.lower()
            symbol = self.symbol_table.lookup(name)
            if not symbol: raise SemanticError(f"Undeclared '{node.lexeme}'")
            node.type = symbol['type']
            return symbol['type']
        if isinstance(node, FuncCallExpr): return self._check_call_stmt(node, is_expr=True)
        if isinstance(node, BinaryOp): return self._check_binary_op(node)
        if isinstance(node, UnaryOp): return self._check_unary_op(node)
        return 'unknown'

    def _check_binary_op(self, node):
        l, r = self._check_expr(node.left), self._check_expr(node.right)
        if node.op in ['+', '-', '*', '/']:
            if l != 'int' or r != 'int': raise SemanticError(f"Math ops require int")
            return 'int'
        if node.op in ['==', '!=', '<', '<=', '>', '>=']:
            if l != r: raise SemanticError(f"Relational ops require same types")
            return 'bool'
        if node.op in ['&&', '||']:
            if l != 'bool' or r != 'bool': raise SemanticError(f"Logic ops require bool")
            return 'bool'
        return 'unknown'

    def _check_unary_op(self, node):
        t = self._check_expr(node.expr)
        if node.op == '!' and t != 'bool': raise SemanticError("NOT requires bool")
        if node.op in ['+','-'] and t != 'int': raise SemanticError("Unary +/- requires int")
        return t


class SemanticError(Exception): pass


def run_analysis(token_stream_list, source_filename):
    tokens = []
    
    if isinstance(token_stream_list, list):
        for t in token_stream_list:
            tokens.append(Token(t['line'], t['tid'], t['kind'], t['lexeme']))
    else:
        for line in token_stream_list.splitlines():
            if not line.strip(): continue
            try:
                parts = line.strip().split(None, 3)
                if len(parts) < 3: continue 
                line_num, tid, kind = parts[0], parts[1], parts[2]
                lexeme = parts[3] if len(parts) > 3 else ''
                if kind.strip() == 'ERROR': continue
                tokens.append(Token(line_num, tid, kind, lexeme))
            except ValueError: continue

    if not tokens:
        print("[ERROR] No tokens found.")
        return
        
    program_name = source_filename

    print(f"\n--- 1. PARSING (CST Generation): {program_name} ---")
    parser = Parser(tokens)
    cst = parser.parse()

    if cst:
        cst_filepath = f"{program_name}_CST.txt"
        with open(cst_filepath, 'w') as f: f.write(cst.traverse())
        print(f"CST written to: {cst_filepath}")

        print(f"\n--- 2. AST GENERATION ---")
        converter = CSTtoAST()
        try:
            ast = converter.build_program(cst)
            
            ast_filepath = f"{program_name}_AST.txt"
            with open(ast_filepath, 'w') as f: f.write(ast.traverse())
            print(f"AST written to: {ast_filepath}")

            print(f"\n--- 3. STATIC SEMANTICS ANALYSIS ---")
            analyzer = SemanticAnalyzer()
            if analyzer.check_program(ast):
                with open(ast_filepath, 'w') as f: f.write(ast.traverse())
                print(f"[INFO] AST updated with semantic info.")
                return ast  # Return AST on success
            else:
                return None  # Semantic errors occurred
            
        except Exception as e:
            print(f"[AST/SEMANTICS ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return None  # Return None if parsing failed

if __name__ == "__main__":
    if len(sys.argv) > 1:
        token_input = sys.argv[1]
        
        with open(token_input, 'r') as f: 
            token_data = f.read()
        
        source_name = token_input
        if len(sys.argv) > 2:
            source_name = sys.argv[2]
            
        run_analysis(token_data, source_name) 
    else:
        print("Usage: python3 parser_semantics.py <tokens_file> [original_filename]")