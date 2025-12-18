class CSTNode:
    """Represents a node in the Concrete Syntax Tree."""
    def __init__(self, name):
        self.name = name 
        self.children = [] 

    def add_child(self, child):
        self.children.append(child)

    def traverse(self, level=0):
        """Generates a string representation of the CST."""
        indent = '  ' * level
        output = f"{indent}{self.name}\n"
        for child in self.children:
            if isinstance(child, CSTNode):
                output += child.traverse(level + 1)
            else:
                
                output += f"{indent}  {child}\n"
        return output



class ASTNode:
    """Base class for all AST nodes."""
    def __init__(self, token=None):
        self.token = token
        self.children = []
        self.type = None 

    def add_child(self, child):
        if child:
            self.children.append(child)

    def __repr__(self):
        return self.__class__.__name__

    def traverse(self, level=0):
        """Generates a readable, indented string representation of the AST."""
        indent = '  ' * level
        output = f"{indent}{self.__repr__()} (Type: {self.type or 'None'})\n"
        for child in self.children:
            output += child.traverse(level + 1)
        return output

class Program(ASTNode):
    def __init__(self, name, declarations, main_func):
        super().__init__()
        self.name = name
        self.declarations = declarations
        self.main_func = main_func
    def __repr__(self):
        return f"Program(Name='{self.name.lexeme}')"
    def traverse(self, level=0):
        indent = '  ' * level
        output = f"{indent}{self.__repr__()}\n"
        output += '  ' * (level + 1) + "Declarations:\n"
        for decl in self.declarations:
            output += decl.traverse(level + 2)
        output += '  ' * (level + 1) + "Main Function:\n"
        output += self.main_func.traverse(level + 2)
        return output

class VarDecl(ASTNode):
    def __init__(self, id_list, token=None):
        super().__init__(token)
        self.id_list = id_list
    def __repr__(self):
        return f"VarDecl({[id.lexeme for id in self.id_list]})"

class FuncDecl(ASTNode):
    def __init__(self, name, params, return_type, body, token=None):
        super().__init__(token)
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body
    def __repr__(self):
        params_str = ', '.join([f'{p.name.lexeme}: {p.type_node.lexeme}' for p in self.params])
        return f"FuncDecl(Name='{self.name.lexeme}', Params=[{params_str}], ReturnType='{self.return_type or 'None'}')"
    def traverse(self, level=0):
        indent = '  ' * level
        output = f"{indent}{self.__repr__()}\n"
        output += '  ' * (level + 1) + "Body (StmtList):\n"
        output += self.body.traverse(level + 2)
        return output

class Param(ASTNode):
    def __init__(self, name, type_node, token=None):
        super().__init__(token)
        self.name = name
        self.type_node = type_node
        self.type = type_node.lexeme
    def __repr__(self):
        return f"Param(Name='{self.name.lexeme}', Type='{self.type}')"

class StmtList(ASTNode):
    def __repr__(self):
        return "StmtList"
    def traverse(self, level=0):
        indent = '  ' * level
        output = f"{indent}StmtList (\n"
        for child in self.children:
            output += child.traverse(level + 1)
        output += indent + ")\n"
        return output

class AssignStmt(ASTNode):
    def __init__(self, target, expr, token=None):
        super().__init__(token)
        self.target = target
        self.add_child(expr)
        self.expr = expr
    def __repr__(self):
        return f"AssignStmt(Target='{self.target.lexeme}')"

class CallStmt(ASTNode):
    def __init__(self, name, args, token=None):
        super().__init__(token)
        self.name = name
        for arg in args:
            self.add_child(arg)
        self.args = args
    def __repr__(self):
        return f"CallStmt(Func='{self.name.lexeme}')"

class PrintStmt(ASTNode):
    def __init__(self, expr, token=None):
        super().__init__(token)
        self.add_child(expr)
        self.expr = expr
    def __repr__(self):
        return "PrintStmt"

class IfStmt(ASTNode):
    def __init__(self, condition, then_block, else_block=None, token=None):
        super().__init__(token)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
        self.add_child(condition)
        self.add_child(then_block)
        if else_block:
            self.add_child(else_block)
    def __repr__(self):
        return "IfStmt"

class WhileStmt(ASTNode):
    def __init__(self, condition, body, token=None):
        super().__init__(token)
        self.condition = condition
        self.body = body
        self.add_child(condition)
        self.add_child(body)
    def __repr__(self):
        return "WhileStmt"

class BreakStmt(ASTNode):
    def __repr__(self):
        return "BreakStmt"

class ReturnStmt(ASTNode):
    def __init__(self, expr=None, token=None):
        super().__init__(token)
        self.expr = expr
        if expr:
            self.add_child(expr)
    def __repr__(self):
        return f"ReturnStmt(HasValue={self.expr is not None})"

class BinaryOp(ASTNode):
    def __init__(self, op_token, left, right, token=None):
        super().__init__(token or op_token)
        self.op = op_token.lexeme
        self.left = left
        self.right = right
        self.add_child(left)
        self.add_child(right)
    def __repr__(self):
        return f"BinaryOp(Op='{self.op}')"

class UnaryOp(ASTNode):
    def __init__(self, op_token, expr, token=None):
        super().__init__(token or op_token)
        self.op = op_token.lexeme
        self.expr = expr
        self.add_child(expr)
    def __repr__(self):
        return f"UnaryOp(Op='{self.op}')"

class Literal(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.value = token.lexeme.strip('"')
        self.type_str = self._determine_type(token.kind)
        self.type = self.type_str
    def _determine_type(self, kind):
        if kind == 'INT': return 'int'
        if kind == 'STR': return 'string'
        if kind == 'BOOL': return 'bool'
        if kind == 'DIR': return 'dir'
        return 'unknown'
    def __repr__(self):
        return f"Literal(Value='{self.value}', Type='{self.type_str}')"

class Identifier(ASTNode):
    def __init__(self, token):
        super().__init__(token)
        self.lexeme = token.lexeme
        self.declaration = None
    def __repr__(self):
        return f"Identifier(Name='{self.lexeme}')"

class FuncCallExpr(CallStmt):
    def __repr__(self):
        return f"FuncCallExpr(Func='{self.name.lexeme}')"

class WorldObject(Identifier):
    def __init__(self, token):
        super().__init__(token)
        self.type = 'world'
    def __repr__(self):
        return "WorldObject"

class AgentObject(Identifier):
    def __init__(self, token):
        super().__init__(token)
        self.type = 'agent'
    def __repr__(self):
        return "AgentObject"