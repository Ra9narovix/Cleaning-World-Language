# Cleaning World Language - Complete Compiler & Interpreter

## Project Overview

The **Cleaning World Language (CWL)** is a simple, Pascal-like procedural language designed to simulate an autonomous cleaning agent moving in a 2D world. This project implements a complete compiler pipeline including lexical analysis, parsing, semantic analysis, and interpretation.

##  Architecture

The compiler follows a traditional multi-phase architecture:

```
Source Code → Lexer → Parser → AST → Semantic Analyzer → Interpreter → Execution
```

### Components

1. **Lexer** (`lexer.py`)
   - Tokenizes source code into a stream of tokens
   - Handles whitespace, comments, and all language tokens
   - Maintains symbol and literal tables

2. **Parser** (`parser_semantics.py`)
   - Recursive Descent LL(1) parser
   - Builds Concrete Syntax Tree (CST)
   - Converts CST to Abstract Syntax Tree (AST)

3. **Semantic Analyzer** (`parser_semantics.py`)
   - Type checking and validation
   - Symbol table management with scoping
   - Built-in function signature validation

4. **Interpreter** (`interpreter.py`)
   - Direct AST interpretation
   - Executes programs with runtime support
   - Manages world and agent state

## Quick Start

### Basic Usage

```bash
# Compile and analyze (no execution)
python main.py program.clean

# Compile, analyze, and execute
python main.py program.clean --execute
```

### Example Program

```clean
program SimpleClean
begin
  var steps;
  func main()
  begin
    world = init_world(5, 5);
    agent = set_agent(world, 0, 0, N);
    while dirt_remaining(world) > 0 do
      if is_dirty(agent) then
        clean(agent);
      else if front_is_blocked(agent) then
        turn_right(agent);
      else
        move_forward(agent);
      end
      steps = steps + 1;
    end
    print("done");
  end
end
```

## 📚 Language Features

### Data Types
- `int` - Integer literals
- `bool` - Boolean literals (`true`, `false`)
- `string` - String literals (double-quoted)
- `dir` - Direction literals (`N`, `E`, `S`, `W`)
- `world` - World object (singleton)
- `agent` - Agent object (singleton)

### Control Structures
- `if-then-else-end` - Conditional statements
- `while-do-end` - Loops
- `break` - Loop termination
- `return` - Function return

### Built-in Functions
- `init_world(width, height)` - Creates a new world
- `set_agent(world, x, y, dir)` - Places agent in world
- `dirt_remaining(world)` - Returns remaining dirt count
- `is_dirty(agent)` - Checks if agent's position has dirt
- `clean(agent)` - Cleans dirt at agent's position
- `move_forward(agent)` - Moves agent forward
- `turn_right(agent)` - Turns agent 90° clockwise
- `front_is_blocked(agent)` - Checks if front is blocked
- `print(value)` - Prints a value

### Operators
- Arithmetic: `+`, `-`, `*`, `/`
- Relational: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Logical: `&&`, `||`, `!`

## Project Structure

```
Cleaning_World_Language/
├── main.py                 # Main entry point
├── lexer.py                # Lexical analyzer
├── parser_semantics.py     # Parser, AST converter, Semantic analyzer
├── interpreter.py          # AST interpreter
├── ast_nodes.py            # AST node definitions
├── sample.clean            # Sample programs
├── test_*.clean            # Test files
└── README.md               # This file
```

##  Testing

The project includes comprehensive test files:

- `test_simple_exec.clean` - Basic execution test
- `test_print.clean` - Print function tests
- `test_world_agent.clean` - World/Agent operations
- `test_control_structures.clean` - Control flow tests
- `test_functions.clean` - User-defined functions
- `test_cleaning_world.clean` - Built-in function tests
- `test_all_tokens.clean` - Complete token coverage

Run tests:
```bash
python main.py test_simple_exec.clean --execute
```

## Language Grammar (EBNF)

```
program ::= PROGRAM ID BEGIN top_items main_decl END
top_items ::= { var_decl | func_decl }
main_decl ::= FUNC MAIN LPAREN RPAREN BEGIN stmt_list END
var_decl ::= VAR id_list SEMI
id_list ::= ID { COMMA ID }
func_decl ::= FUNC ID LPAREN [ params ] RPAREN [ COLON type ] BEGIN stmt_list END
params ::= param { COMMA param }
param ::= ID COLON type
type ::= INT | BOOL | STRING
stmt_list ::= { stmt }
stmt ::= assign_stmt | call_stmt | print_stmt | if_stmt | while_stmt | break_stmt | return_stmt
assign_stmt ::= (ID | WORLD | AGENT) ASSIGN expr SEMI
call_stmt ::= ID LPAREN [ args ] RPAREN SEMI
print_stmt ::= PRINT LPAREN expr RPAREN SEMI
if_stmt ::= IF expr THEN stmt_list [ ELSE stmt_list ] END
while_stmt ::= WHILE expr DO stmt_list END
break_stmt ::= BREAK SEMI
return_stmt ::= RETURN [ expr ] SEMI
args ::= expr { COMMA expr }
expr ::= or_expr
or_expr ::= and_expr { OR and_expr }
and_expr ::= rel_expr { AND rel_expr }
rel_expr ::= add_expr [ rel_op add_expr ]
rel_op ::= EQ | NEQ | LT | LE | GT | GE
add_expr ::= mul_expr { (PLUS | MINUS) mul_expr }
mul_expr ::= unary { (STAR | SLASH) unary }
unary ::= NOT unary | primary
primary ::= INT | STR | BOOL | DIR | ID | WORLD | AGENT | call | LPAREN expr RPAREN
```

## Implementation Details

### Lexer
- Uses Python `re` module for pattern matching
- Longest-match token recognition
- Maintains line numbers for error reporting
- Handles comments and whitespace

### Parser
- Recursive Descent LL(1) implementation
- Direct grammar-to-code mapping
- Builds CST during parsing
- Converts CST to simplified AST

### Semantic Analyzer
- Hierarchical symbol table with scoping
- Type checking and validation
- Built-in function signature checking
- Scope resolution for identifiers

### Interpreter
- Direct AST interpretation
- Runtime environment with variable storage
- Function call stack for local scopes
- World and agent state management

## Output Files

When processing a program, the compiler generates:
- `*_CST.txt` - Concrete Syntax Tree representation
- `*_AST.txt` - Abstract Syntax Tree representation

## Notes

- Variables must be declared at the top level (before functions)
- `world` and `agent` are global singletons accessible from any function
- All keywords are case-sensitive and must be lowercase
- While loops have a safety limit of 100,000 iterations

## Authors

- Amr Ghazzali
- Ayman ElAkkaoui
- Ghali Baghdad Jamai
- Ihab Kassimi

## License

This project is part of CSC 3315 Languages and Compilers course work.

---

**Status**:  Fully functional compiler and interpreter
**Version**: 1.0
