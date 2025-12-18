import sys
import os
import lexer
from parser_semantics import run_analysis
from interpreter import Interpreter, RuntimeError

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <filename.clean> [--execute]")
        sys.exit(1)
        
    filename = sys.argv[1]
    execute = '--execute' in sys.argv or '-e' in sys.argv
    
    if not os.path.exists(filename):
        print(f"[ERROR] File '{filename}' not found.")
        sys.exit(1)

    print(f"--- COMPILING: {filename} ---")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        if not source_code.strip():
            print("[ERROR] Input file is empty.")
            sys.exit(1)
            
        tokens = lexer.tokenize(source_code)
        
        if not tokens:
            print("[ERROR] Lexer found no tokens.")
            sys.exit(1)
            
    except Exception as e:
        print(f"[LEXER ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    ast = run_analysis(tokens, filename)
    
    if ast is None:
        print("\n[ERROR] Failed to generate valid AST. Execution cannot proceed.")
        if execute:
            print("[INFO] Fix semantic errors above to enable execution.")
        sys.exit(1)
    
    # Execute the program if requested and AST is valid
    if execute and ast:
        print(f"\n--- 4. EXECUTION ---")
        try:
            interpreter = Interpreter()
            print("[DEBUG] Starting execution...")
            interpreter.execute(ast)
            print("[INFO] Execution completed successfully.")
        except KeyboardInterrupt:
            print("\n[INFO] Execution interrupted by user.")
            sys.exit(1)
        except RuntimeError as e:
            print(f"[RUNTIME ERROR] {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            print(f"[EXECUTION ERROR] {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()
