# Simple Python Shell (PyShell)

This project is a functional **Command Line Interpreter (CLI)** built with Python. It mimics the core behavior of a Unix-like shell, supporting built-in commands and the execution of external system programs via subprocesses.

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

### 2. External Command Execution
If a command is not a builtin, the shell searches the system's `PATH` (using `shutil.which`) and attempts to execute it. This allows you to run standard tools like `ls`, `grep`, or `cat` directly from this shell.

---

## ## Getting Started

### Prerequisites
* **Python 3.8+**: The script uses the "walrus operator" (`:=`) in the `type` command logic.

### How to Run
1.  Clone this repository or download the `APP.py` file.
2.  Open your terminal or command prompt.
3.  Run the script:
    ```bash
    python APP.py
    ```
4.  You will see a `$ ` prompt where you can begin entering commands.

---

## ## Project Structure

| File | Description |
| :--- | :--- |
| `APP.py` | The main script containing the command loop, tokenization, and logic. |

---

## ## Technical Highlights

* **Tokenization**: Uses `command.split(" ")` to parse user input into manageable tokens.
* **Process Management**: Utilizes the `subprocess` module to bridge the gap between Python and system-level applications.
* **Directory Handling**: Employs `os.chdir` and `os.getcwd` for seamless filesystem navigation.
* **Path Resolution**: Uses `shutil` to dynamically find the location of external binaries.

---

> **Note:** This shell is currently a foundational project. It treats single spaces as delimiters and does not yet support advanced features like piping (`|`) or output redirection (`>`).