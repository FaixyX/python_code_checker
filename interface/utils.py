"""
Utility functions for code execution and evaluation
"""
import subprocess
import tempfile
import os
import re


def normalize_output(output):
    """Normalize output for comparison (handles whitespace, line endings, etc.)"""
    if not output:
        return ""
    # Remove extra whitespace and normalize line endings
    output = re.sub(r'\r\n', '\n', output)  # Windows to Unix
    output = re.sub(r'\r', '\n', output)    # Mac to Unix
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in output.split('\n')]
    # Remove empty lines at the end
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines)


def get_file_extension(language):
    """Return the appropriate file extension for the programming language"""
    language = language.lower()
    extensions = {
        'python': '.py',
        'python3': '.py',
        'java': '.java',
        'javascript': '.js',
        'node': '.js',
        'nodejs': '.js',
        'c': '.c',
        'c++': '.cpp',
        'cpp': '.cpp',
        'c#': '.cs',
        'csharp': '.cs',
        'php': '.php',
        'ruby': '.rb',
        'go': '.go',
        'rust': '.rs',
    }
    return extensions.get(language, '.txt')


def get_execution_command(language, file_path):
    """Return the appropriate command to execute code in the given language"""
    language = language.lower()
    
    if language in ['python', 'python3']:
        return ['python3', file_path]
    elif language == 'java':
        # Java requires compilation first
        # For simplicity, assume the file is already compiled
        # In production, you'd want to handle compilation
        class_name = os.path.splitext(os.path.basename(file_path))[0]
        return ['java', class_name]
    elif language in ['javascript', 'node', 'nodejs']:
        return ['node', file_path]
    elif language == 'c':
        # C requires compilation first
        # For simplicity, assume the file is already compiled
        executable = os.path.splitext(file_path)[0]
        return [executable]
    elif language in ['c++', 'cpp']:
        # C++ requires compilation first
        executable = os.path.splitext(file_path)[0]
        return [executable]
    elif language in ['c#', 'csharp']:
        return ['dotnet', 'run', '--project', file_path]
    elif language == 'php':
        return ['php', file_path]
    elif language == 'ruby':
        return ['ruby', file_path]
    elif language == 'go':
        return ['go', 'run', file_path]
    elif language == 'rust':
        return ['rustc', file_path, '&&', os.path.splitext(file_path)[0]]
    else:
        return None


def run_code(code, input_data, expected_output, language):
    """
    Execute code in various languages and compare output with expected output.
    This is a simple implementation and should be replaced with a secure sandbox in production.
    """
    try:
        # Create a temporary file to hold the code
        with tempfile.NamedTemporaryFile(suffix=get_file_extension(language), delete=False) as temp_file:
            temp_file.write(code.encode('utf-8'))
            temp_file_path = temp_file.name

        # Create a temporary file for input if needed
        input_file_path = None
        if input_data:
            with tempfile.NamedTemporaryFile(delete=False) as input_file:
                input_file.write(input_data.encode('utf-8'))
                input_file_path = input_file.name

        # Determine command based on language
        command = get_execution_command(language, temp_file_path)
        if not command:
            print(f"Unsupported language: {language}")
            return False

        # Execute the code with appropriate command
        if input_data:
            # Use input file if input data is provided
            with open(input_file_path, 'r') as input_file:
                process = subprocess.run(
                    command,
                    stdin=input_file,
                    text=True,
                    capture_output=True,
                    timeout=10  # Increased timeout for more complex programs
                )
        else:
            # Run without input if none provided
            process = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=10
            )

        # Clean up temporary files
        os.unlink(temp_file_path)
        if input_file_path:
            os.unlink(input_file_path)

        # Check result
        actual_output = process.stdout.strip()
        expected_output = expected_output.strip()
        
        # For debugging
        print(f"Actual output: {actual_output}")
        print(f"Expected output: {expected_output}")
        print(f"Process return code: {process.returncode}")
        if process.stderr:
            print(f"Process errors: {process.stderr}")
        
        # Allow for different line endings and whitespace
        return normalize_output(actual_output) == normalize_output(expected_output)
    
    except subprocess.TimeoutExpired:
        print("Code execution timed out")
        return False
    except Exception as e:
        print(f"Error during code execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

