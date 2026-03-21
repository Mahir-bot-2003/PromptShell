# Simple Shell

This project is a functional **Command Line Interpreter (CLI)** built with Python. It mimics the core behavior of a Unix-like shell, supporting built-in commands and the execution of external system programs via subprocesses and helps to understand how the scenes work behind the all commands and try to build it from the scratch.

---

## ## Features

The shell provides several core functionalities:

### 1. Built-in Commands
The following commands are handled directly by the script logic:
* `echo`: Prints arguments to the standard output.
* `pwd`: Prints the absolute path of the current working directory.
* `cd`: Changes the current directory (supports `~` for the home directory).
* `type`: Identifies if a command is a shell builtin or an external executable.
* `exit`: Safely terminates the shell session.
* More will be updated 

## ## Getting Started

### Prerequisites
* **Python 3.8+**: The script uses the "walrus operator" (`:=`) in the `type` command logic.

### How to Run
1.  Clone this repository or download the `APP.py` file.
2.  Open your terminal or command prompt.
3.  Go to you path in the command prompt or terminal
4.  Run the script:
    ```bash
    python APP.py
    ```
5.  You will see a `$ ` prompt where you can begin entering commands.

---

## ## Technical Highlights

* **Tokenization**: Uses `command.split(" ")` to parse user input into manageable tokens.
* **Process Management**: Utilizes the `subprocess` module to bridge the gap between Python and system-level applications.
* **Directory Handling**: Employs `os.chdir` and `os.getcwd` for seamless filesystem navigation.
* **Path Resolution**: Uses `shutil` to dynamically find the location of external binaries.

---
## ## Updates
* Enhance the file directory files
* Added the append mode in the stderr and stdout.
> **Note:** This shell is currently a foundational project. It treats single spaces as delimiters and does not yet support advanced features like piping (`|`) or output redirection (`>`).
