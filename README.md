# 🖥️ Simple Shell (Python CLI)

This project is a **custom Unix-like Command Line Interpreter (Shell)** built from scratch using Python.  
It replicates core terminal behavior including command parsing, execution of system programs, built-in commands, and I/O redirection.

The goal of this project is to **understand how real shells (like Bash/Zsh) work internally** — from parsing input to managing processes and file descriptors.

---

##  Features

### Built-in Commands
The shell directly implements the following commands:
* `echo` → Prints arguments to standard output  
* `pwd` → Displays the current working directory  
* `cd` → Changes directory (supports `~` for home)  
* `type` → Identifies whether a command is builtin or external  
* `exit` → Terminates the shell session  

### Input Parsing (Advanced)
Uses `shlex.split()` for robust tokenization, handling:
* Quoted strings (`"hello world"`, `'text'`)
* Proper argument separation
* Escaped characters and complex spacing

### I/O Redirection
Supports standard Unix-style redirection:

| Operator | Description |
| :--- | :--- |
| `>` | Redirect stdout (overwrite) |
| `>>` | Redirect stdout (append) |
| `2>` | Redirect stderr (overwrite) |
| `2>>` | Redirect stderr (append) |

**Example:**
```bash
echo "hello world" > file.txt
ls non_existent_folder 2> error.log
```

### Tab Completion
Built using the `readline` module to provide:
* Autocompletion for built-in commands
* An interactive, user-friendly CLI experience

### File & Directory Handling
* Automatically creates directories for redirected outputs
* Handles absolute and relative paths
* Expands `~` to the user's home directory

---

## 🛠️ Tech Stack

* **Language:** Python 3.8+
* **Core Modules:** * `subprocess`: Process execution
    * `os`: File system operations
    * `shlex`: Robust command parsing
    * `shutil`: PATH resolution and executable lookup
    * `readline`: CLI interactivity and completion

---

## 📦 Getting Started

### Prerequisites
* Python 3.8 or higher

### Installation & Execution
1. Clone this repository:
   ```bash
   git clone [https://github.com/yourusername/simple-shell-python.git](https://github.com/yourusername/simple-shell-python.git)
   cd simple-shell-python
   ```
2. Run the Shell:
   ```bash
   python APP.py
   ```
3. You’ll see the prompt:
   ```bash
   $ 
   ```
   Start typing commands!

---

## 🧠 Technical Highlights

* **REPL Design:** Designed a Read–Eval–Print Loop from scratch.
* **Process Management:** Built a mini process execution system using `subprocess.run()`.
* **Manual I/O Handling:** Implemented file descriptor redirection logic.
* **Path Resolution:** Used `shutil.which()` to replicate shell-like executable lookups across the system.

---

## Limitations (Current)

This is a foundational system-level project. Some advanced features are currently not supported:
* ❌ Pipelines (`|`)
* ❌ Command chaining (`&&`, `||`)
* ❌ Environment variables (`$HOME`, etc.)
* ❌ Job control (`fg`, `bg`)
* ❌ History navigation (↑/↓ arrows)
---

## Future Improvements

- [ ] **Pipeline support:** `cmd1 | cmd2`
- [ ] **Command history:** Persistent history across sessions
- [ ] **Environment variable expansion:** `$VAR` support
- [ ] **Signal handling:** Proper `Ctrl+C` management
- [ ] **Configuration:** Support for a `.myshellrc` file
- [ ] **AI integrations**

---

## Why This Project Matters

This project demonstrates:
* Deep understanding of **Operating System fundamentals**.
* Hands-on experience with **process management** and file descriptors.
* Ability to build real-world CLI tools.
* Strong grasp of **parsing** and system interaction.

---
