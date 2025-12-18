"""
Cleaning World Language Interpreter
Implements direct AST interpretation and execution
"""
import random
from ast_nodes import *

# Direction vectors: N, E, S, W
DIRECTIONS = {'N': (-1, 0), 'E': (0, 1), 'S': (1, 0), 'W': (0, -1)}
DIR_ORDER = ['N', 'E', 'S', 'W']  # For turning right

class CleaningWorld:
    """Represents a 2D cleaning world grid"""
    EMPTY = 0
    OBSTACLE = 1
    DIRT = 2
    ENTRY = 3
    EXIT = 4
    
    def __init__(self, width, height):
        if width < 3 or height < 3:
            raise ValueError("World dimensions must be at least 3x3")
        self.width = width
        self.height = height
        self.grid = [[self.EMPTY for _ in range(width)] for _ in range(height)]
        self.entry_pos = None
        self.exit_positions = []
        self._initialize_world()
    
    def _initialize_world(self):
        """Initialize world with obstacles and dirt in a simple pattern"""
        # Create borders (except entry/exit points)
        for i in range(self.height):
            for j in range(self.width):
                if i == 0 or i == self.height - 1 or j == 0 or j == self.width - 1:
                    self.grid[i][j] = self.OBSTACLE
        
        # Set entry point (top-left corner, opening)
        self.entry_pos = (0, 0)
        self.grid[0][0] = self.ENTRY
        
        # Create some exits (bottom and right sides)
        if self.height > 2:
            self.exit_positions.append((self.height - 1, self.width // 2))
            self.grid[self.height - 1][self.width // 2] = self.EXIT
        if self.width > 2:
            self.exit_positions.append((self.height // 2, self.width - 1))
            self.grid[self.height // 2][self.width - 1] = self.EXIT
        
        # Place obstacles in interior (sparse pattern)
        obstacle_count = (self.width * self.height) // 10
        for _ in range(obstacle_count):
            i = random.randint(1, self.height - 2)
            j = random.randint(1, self.width - 2)
            if self.grid[i][j] == self.EMPTY:
                self.grid[i][j] = self.OBSTACLE
        
        # Place dirt (most empty cells get dirt)
        dirt_count = (self.width * self.height) // 3
        placed = 0
        attempts = 0
        while placed < dirt_count and attempts < dirt_count * 3:
            i = random.randint(1, self.height - 2)
            j = random.randint(1, self.width - 2)
            if self.grid[i][j] == self.EMPTY:
                self.grid[i][j] = self.DIRT
                placed += 1
            attempts += 1
    
    def is_valid(self, row, col):
        """Check if position is within bounds"""
        return 0 <= row < self.height and 0 <= col < self.width
    
    def is_blocked(self, row, col):
        """Check if position is blocked by obstacle or wall"""
        if not self.is_valid(row, col):
            return True
        return self.grid[row][col] == self.OBSTACLE
    
    def is_dirt(self, row, col):
        """Check if position has dirt"""
        if not self.is_valid(row, col):
            return False
        return self.grid[row][col] == self.DIRT
    
    def clean(self, row, col):
        """Clean dirt at position"""
        if self.is_valid(row, col) and self.grid[row][col] == self.DIRT:
            self.grid[row][col] = self.EMPTY
    
    def dirt_remaining(self):
        """Count remaining dirt"""
        count = 0
        for i in range(self.height):
            for j in range(self.width):
                if self.grid[i][j] == self.DIRT:
                    count += 1
        return count
    
    def is_exit(self, row, col):
        """Check if position is an exit"""
        return (row, col) in self.exit_positions
    
    def __repr__(self):
        return f"CleaningWorld({self.width}x{self.height})"


class Agent:
    """Represents the cleaning agent"""
    def __init__(self, world, row, col, direction):
        self.world = world
        self.row = row
        self.col = col
        self.direction = direction  # 'N', 'E', 'S', 'W'
        self.dirt_collected = 0
    
    def get_front_position(self):
        """Get position in front of agent"""
        dr, dc = DIRECTIONS[self.direction]
        return (self.row + dr, self.col + dc)
    
    def front_is_blocked(self):
        """Check if front is blocked"""
        fr, fc = self.get_front_position()
        return self.world.is_blocked(fr, fc)
    
    def move_forward(self):
        """Move agent forward one step"""
        fr, fc = self.get_front_position()
        if not self.world.is_blocked(fr, fc):
            self.row = fr
            self.col = fc
            return True
        return False
    
    def turn_right(self):
        """Turn agent 90 degrees clockwise"""
        idx = DIR_ORDER.index(self.direction)
        self.direction = DIR_ORDER[(idx + 1) % 4]
    
    def is_dirty(self):
        """Check if current position has dirt"""
        return self.world.is_dirt(self.row, self.col)
    
    def clean(self):
        """Clean dirt at current position"""
        if self.world.is_dirt(self.row, self.col):
            self.world.clean(self.row, self.col)
            self.dirt_collected += 1
            return True
        return False
    
    def __repr__(self):
        return f"Agent({self.row}, {self.col}, {self.direction})"


class RuntimeError(Exception):
    """Runtime execution error"""
    pass


class Interpreter:
    """Interpreter for Cleaning World Language AST"""
    
    def __init__(self):
        self.global_vars = {}  # Global variable storage
        self.functions = {}  # Function definitions
        self.call_stack = []  # Function call stack (for local variables)
        self.world = None
        self.agent = None
        self.return_value = None
        self.break_flag = False
        self.max_loop_iterations = 100000  # Safety limit to prevent infinite loops
    
    def execute(self, ast):
        """Main entry point: execute a Program AST"""
        if not isinstance(ast, Program):
            raise RuntimeError("Expected Program AST node")
        
        # Register all function declarations
        for decl in ast.declarations:
            if isinstance(decl, FuncDecl):
                self.functions[decl.name.lexeme] = decl
        
        # Register global variables
        for decl in ast.declarations:
            if isinstance(decl, VarDecl):
                for id_token in decl.id_list:
                    self.global_vars[id_token.lexeme.lower()] = 0  # Default to 0 (int)
        
        # Execute main function (it's stored in ast.main_func, not in functions dict)
        if ast.main_func is None:
            raise RuntimeError("No main function found")
        
        try:
            self._execute_function(ast.main_func, [])
        except KeyboardInterrupt:
            raise
        except Exception as e:
            import traceback
            print(f"[INTERNAL ERROR] {e}")
            traceback.print_exc()
            raise
    
    def _execute_function(self, func_decl, args):
        """Execute a function with given arguments"""
        # Create new scope for function
        local_vars = {}
        
        # Bind parameters (normalize to lowercase for consistency)
        for param, arg_value in zip(func_decl.params, args):
            local_vars[param.name.lexeme.lower()] = arg_value
        
        # Push scope onto stack
        self.call_stack.append(local_vars)
        
        try:
            if func_decl.body is None:
                raise RuntimeError(f"Function '{func_decl.name.lexeme}' has no body")
            self._execute_stmt_list(func_decl.body)
            return self.return_value
        finally:
            # Pop scope
            self.call_stack.pop()
            self.return_value = None
    
    def _get_variable(self, name):
        """Get variable value from current scope or global"""
        # Normalize name to lowercase for consistency
        name = name.lower()
        # Check local scope (current function)
        if self.call_stack and name in self.call_stack[-1]:
            return self.call_stack[-1][name]
        # Check global scope
        if name in self.global_vars:
            return self.global_vars[name]
        raise RuntimeError(f"Undeclared variable: {name}")
    
    def _set_variable(self, name, value):
        """Set variable value in current scope or global"""
        # Normalize name to lowercase for consistency
        name = name.lower()
        # Try local scope first
        if self.call_stack and name in self.call_stack[-1]:
            self.call_stack[-1][name] = value
        else:
            # Set in global scope
            self.global_vars[name] = value
    
    def _execute_stmt_list(self, stmt_list):
        """Execute a list of statements"""
        if stmt_list is None:
            return
        if not hasattr(stmt_list, 'children') or stmt_list.children is None:
            return
        self.break_flag = False
        for stmt in stmt_list.children:
            if stmt is None:
                continue
            self._execute_stmt(stmt)
            if self.break_flag:
                break
            if self.return_value is not None:
                break
    
    def _execute_stmt(self, stmt):
        """Execute a single statement"""
        if isinstance(stmt, AssignStmt):
            self._execute_assign(stmt)
        elif isinstance(stmt, CallStmt):
            self._execute_call_stmt(stmt)
        elif isinstance(stmt, PrintStmt):
            self._execute_print(stmt)
        elif isinstance(stmt, IfStmt):
            self._execute_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self._execute_while(stmt)
        elif isinstance(stmt, BreakStmt):
            self.break_flag = True
        elif isinstance(stmt, ReturnStmt):
            self._execute_return(stmt)
        else:
            raise RuntimeError(f"Unknown statement type: {type(stmt)}")
    
    def _execute_assign(self, stmt):
        """Execute assignment statement"""
        # Normalize to lowercase for world/agent handling
        target_name = stmt.target.lexeme.lower()
        value = self._evaluate_expr(stmt.expr)
        self._set_variable(target_name, value)
        
        # Special handling for world and agent
        if target_name == 'world':
            if not isinstance(value, CleaningWorld):
                raise RuntimeError("world must be assigned a CleaningWorld object")
            self.world = value
        elif target_name == 'agent':
            if not isinstance(value, Agent):
                raise RuntimeError("agent must be assigned an Agent object")
            self.agent = value
    
    def _execute_call_stmt(self, stmt):
        """Execute function call statement"""
        func_name = stmt.name.lexeme
        args = [self._evaluate_expr(arg) for arg in stmt.args]
        
        # Check built-in functions
        if func_name in BUILTIN_FUNCTIONS:
            return self._execute_builtin(func_name, args)
        
        # Check user-defined functions
        if func_name not in self.functions:
            raise RuntimeError(f"Undeclared function: {func_name}")
        
        func_decl = self.functions[func_name]
        if len(args) != len(func_decl.params):
            raise RuntimeError(f"Function {func_name} expects {len(func_decl.params)} arguments, got {len(args)}")
        
        self._execute_function(func_decl, args)
        return self.return_value
    
    def _execute_builtin(self, name, args):
        """Execute built-in function"""
        if name == 'init_world':
            width, height = args[0], args[1]
            return CleaningWorld(width, height)
        
        elif name == 'set_agent':
            world, x, y, direction = args[0], args[1], args[2], args[3]
            if not isinstance(world, CleaningWorld):
                raise RuntimeError("set_agent: first argument must be a world")
            # Handle direction (could be string or have lexeme attribute)
            if isinstance(direction, str):
                dir_char = direction.upper()
            elif hasattr(direction, 'lexeme'):
                dir_char = direction.lexeme.upper()
            else:
                dir_char = str(direction).upper()
            
            if dir_char not in ['N', 'E', 'S', 'W']:
                raise RuntimeError(f"set_agent: invalid direction '{dir_char}', must be N, E, S, or W")
            
            agent = Agent(world, x, y, dir_char)
            return agent
        
        elif name == 'dirt_remaining':
            world = args[0]
            if not isinstance(world, CleaningWorld):
                raise RuntimeError("dirt_remaining: argument must be a world")
            return world.dirt_remaining()
        
        elif name == 'is_dirty':
            agent = args[0]
            if not isinstance(agent, Agent):
                raise RuntimeError("is_dirty: argument must be an agent")
            return agent.is_dirty()
        
        elif name == 'clean':
            agent = args[0]
            if not isinstance(agent, Agent):
                raise RuntimeError("clean: argument must be an agent")
            agent.clean()
            return None
        
        elif name == 'move_forward':
            agent = args[0]
            if not isinstance(agent, Agent):
                raise RuntimeError("move_forward: argument must be an agent")
            agent.move_forward()
            return None
        
        elif name == 'turn_right':
            agent = args[0]
            if not isinstance(agent, Agent):
                raise RuntimeError("turn_right: argument must be an agent")
            agent.turn_right()
            return None
        
        elif name == 'front_is_blocked':
            agent = args[0]
            if not isinstance(agent, Agent):
                raise RuntimeError("front_is_blocked: argument must be an agent")
            return agent.front_is_blocked()
        
        elif name == 'print':
            value = args[0]
            if isinstance(value, bool):
                print(str(value).lower())
            else:
                print(value)
            return None
        
        else:
            raise RuntimeError(f"Unknown built-in function: {name}")
    
    def _execute_print(self, stmt):
        """Execute print statement"""
        value = self._evaluate_expr(stmt.expr)
        if isinstance(value, bool):
            print(str(value).lower())
        else:
            print(value)
    
    def _execute_if(self, stmt):
        """Execute if statement"""
        condition = self._evaluate_expr(stmt.condition)
        if not isinstance(condition, bool):
            raise RuntimeError("If condition must be boolean")
        
        if condition:
            if stmt.then_block:
                self._execute_stmt_list(stmt.then_block)
        else:
            if stmt.else_block:
                self._execute_stmt_list(stmt.else_block)
    
    def _execute_while(self, stmt):
        """Execute while statement"""
        iteration_count = 0
        while True:
            iteration_count += 1
            if iteration_count > self.max_loop_iterations:
                raise RuntimeError(f"While loop exceeded maximum iterations ({self.max_loop_iterations}). Possible infinite loop.")
            
            condition = self._evaluate_expr(stmt.condition)
            if not isinstance(condition, bool):
                raise RuntimeError("While condition must be boolean")
            
            if not condition:
                break
            
            self.break_flag = False
            self._execute_stmt_list(stmt.body)
            
            if self.break_flag or self.return_value is not None:
                self.break_flag = False
                break
    
    def _execute_return(self, stmt):
        """Execute return statement"""
        if stmt.expr:
            self.return_value = self._evaluate_expr(stmt.expr)
        else:
            self.return_value = None
    
    def _evaluate_expr(self, expr):
        """Evaluate an expression and return its value"""
        if isinstance(expr, Literal):
            return self._evaluate_literal(expr)
        elif isinstance(expr, Identifier):
            return self._evaluate_identifier(expr)
        elif isinstance(expr, WorldObject):
            if self.world is None:
                raise RuntimeError("world not initialized")
            return self.world
        elif isinstance(expr, AgentObject):
            if self.agent is None:
                raise RuntimeError("agent not initialized")
            return self.agent
        elif isinstance(expr, BinaryOp):
            return self._evaluate_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            return self._evaluate_unary_op(expr)
        elif isinstance(expr, FuncCallExpr):
            return self._evaluate_func_call(expr)
        else:
            raise RuntimeError(f"Unknown expression type: {type(expr)}")
    
    def _evaluate_literal(self, literal):
        """Evaluate a literal value"""
        if literal.type == 'int':
            return int(literal.value)
        elif literal.type == 'string':
            return literal.value
        elif literal.type == 'bool':
            return literal.value.lower() == 'true'
        elif literal.type == 'dir':
            # Direction is stored as the lexeme value (N, E, S, W)
            return literal.value.upper() if isinstance(literal.value, str) else str(literal.value).upper()
        else:
            raise RuntimeError(f"Unknown literal type: {literal.type}")
    
    def _evaluate_identifier(self, ident):
        """Evaluate an identifier (variable lookup)"""
        # _get_variable already normalizes to lowercase
        return self._get_variable(ident.lexeme)
    
    def _evaluate_func_call(self, expr):
        """Evaluate function call expression"""
        func_name = expr.name.lexeme
        args = [self._evaluate_expr(arg) for arg in expr.args]
        
        # Check built-in functions
        if func_name in BUILTIN_FUNCTIONS:
            return self._execute_builtin(func_name, args)
        
        # Check user-defined functions
        if func_name not in self.functions:
            raise RuntimeError(f"Undeclared function: {func_name}")
        
        func_decl = self.functions[func_name]
        if len(args) != len(func_decl.params):
            raise RuntimeError(f"Function {func_name} expects {len(func_decl.params)} arguments, got {len(args)}")
        
        return self._execute_function(func_decl, args)
    
    def _evaluate_binary_op(self, op):
        """Evaluate binary operation"""
        left = self._evaluate_expr(op.left)
        right = self._evaluate_expr(op.right)
        operator = op.op
        # Handle case where operator might be a Token object
        if hasattr(operator, 'lexeme'):
            operator = operator.lexeme
        
        # Arithmetic operations
        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            if right == 0:
                raise RuntimeError("Division by zero")
            return left // right  # Integer division
        
        # Relational operations
        elif operator == '==':
            return left == right
        elif operator == '!=':
            return left != right
        elif operator == '<':
            return left < right
        elif operator == '<=':
            return left <= right
        elif operator == '>':
            return left > right
        elif operator == '>=':
            return left >= right
        
        # Logical operations
        elif operator == '&&':
            return bool(left) and bool(right)
        elif operator == '||':
            return bool(left) or bool(right)
        else:
            raise RuntimeError(f"Unknown binary operator: {operator}")
    
    def _evaluate_unary_op(self, op):
        """Evaluate unary operation"""
        expr_value = self._evaluate_expr(op.expr)
        operator = op.op
        # Handle case where operator might be a Token object
        if hasattr(operator, 'lexeme'):
            operator = operator.lexeme
        
        if operator == '!':
            return not bool(expr_value)
        elif operator == '+':
            return +expr_value
        elif operator == '-':
            return -expr_value
        else:
            raise RuntimeError(f"Unknown unary operator: {operator}")


# Import BUILTIN_FUNCTIONS from parser_semantics
try:
    from parser_semantics import BUILTIN_FUNCTIONS
except ImportError:
    # Fallback definition
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

