# 🖥️ Promptshell (Python CLI)

This project is a **custom Unix-like Command Line Interpreter (Shell)** built from scratch using Python.  
It replicates core terminal behavior including command parsing, execution of system programs, built-in commands, and I/O redirection.

The goal of this project is to **understand how real shells (like Bash/Zsh) work internally** — from parsing input to managing processes and file descriptors.

---

## ✨ Features

### Built-in Commands
The shell directly implements the following commands:
* `echo` → Prints arguments to standard output  
* `pwd` → Displays the current working directory  
* `cd` → Changes directory (supports `~` for home)  
* `ls` → Cross-platform directory listing with sizes and permissions
* `type` → Identifies whether a command is builtin or external  
* `export` / `unset` → Manage environment variables
* `history` → View and manage your command history
* `setup-ai` → Interactive setup for Gemini AI integration
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
| `<` | Redirect stdin from file |

**Example:**
```bash
echo "hello world" > file.txt
ls non_existent_folder 2> error.log
```

### Pipelines & Variables
* Chain multiple commands using pipes: `cat file.txt | sort | uniq`
* Expand environment variables: `echo $HOME` or `echo ${VAR}`

### Natural Language Engine (Smart Engine)
Promptshell understands plain English natively.
* **Offline Rules**: Instantly translates common phrases offline (e.g. `show me all python files` → `find . -name "*.py" -type f`).
* **Gemini AI Fallback**: If the offline rules don't match, it automatically asks Google's Gemini AI to write the exact command for you (Requires free API key via `setup-ai`).

### Tab Completion & History
Built using the `readline` module (or `pyreadline3` on Windows) to provide:
* Autocompletion for built-in commands
* Persistent history navigation (↑/↓ arrows)

---

## 🛠️ Tech Stack

* **Language:** Python 3.8+
* **Core Modules:** 
    * `subprocess`: Process execution
    * `os`: File system operations
    * `shlex`: Robust command parsing
    * `shutil`: PATH resolution and executable lookup
    * `readline`: CLI interactivity and completion
    * `urllib`: Native HTTP requests for AI integration (Zero external dependencies)

---

## 📦 Getting Started

### Prerequisites
* Python 3.8 or higher
* Windows/Linux/macOS supported natively

### Installation & Execution
1. Clone this repository:
   ```bash
   git clone https://github.com/Mahir-bot-2003/simple-shell-python.git
   cd simple-shell-python
   ```
2. Run the Shell:
   ```bash
   python -m app.main
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
* **Manual I/O Handling:** Implemented file descriptor redirection logic and pipeline (`os.pipe()`) routing.
* **Hybrid Natural Language Processing:** Fuses regex-based synonym extraction with an LLM fallback layer.

---

## Future Improvements

- [x] **Pipeline support:** `cmd1 | cmd2`
- [x] **Command history:** Persistent history across sessions
- [x] **Environment variable expansion:** `$VAR` support
- [x] **AI integrations**: Natural language and Gemini fallback
- [x] **Cross-platform**: Built-in Windows-compatible `ls`
- [ ] **Command chaining:** `&&`, `||`
- [ ] **Job control:** `fg`, `bg`, `&`
- [ ] **Configuration:** Support for a `.promptshellrc` file

---

## Why This Project Matters

This project demonstrates:
* Deep understanding of **Operating System fundamentals**.
* Hands-on experience with **process management**, file descriptors, and pipes.
* Ability to build real-world CLI tools.
* Strong grasp of **parsing** and system interaction.
