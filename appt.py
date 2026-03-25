import sys  #talks to the system
import shutil #file and program
import subprocess #run other porgrams
import os  #plays with the directory
import shlex #shelex handles automatically spaces and splits better
import readline #use to make cli input smarter and interative

_last_prefix = None
_tab_count = 0

def get_all_commands_for_tab(): #this function will help to find the all command in a folder and show it using tab
    cmds = {"echo", "exit"}
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        #.get("PATH ") gives all the path 
        #os.pathsep(Separator between folders)
        if not folder:
            continue
        try:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if os.path.isfile(full) and os.access(full, os.X_OK):
                    #this lines check whether file is not not a folder and is it executable ot not
                    cmds.add(name)
        except OSError:
            pass
    return sorted(cmds)

#this function is used bexuase shell can auto complete as much as possible WITHOUT guessing wrong
def longest_common_prefix(words):
    if not words:
        return ""

    for i in range(len(words[0])):
        char = words[0][i]

        for word in words:
            if i >= len(word) or word[i] != char:
                return words[0][:i]

    return words[0]

def command_completer(text, state):
    global _last_prefix, _tab_count
    line = readline.get_line_buffer()
    if " " in line:
        last_prefix = None
        _tab_count = 0
        return None

    if state != 0:
        return None
    
    matches = [c for c in get_all_commands_for_tab() if c.startswith(text)]
    matches.sort()

    if not matches:
        _last_prefix = None
        _tab_count = 0
        return None
    
    if len(matches) == 1:
        _last_prefix = None
        _tab_count = 0
        return matches[0] + " "
    
    lcp = longest_common_prefix(matches)

    if len(lcp) > len(text):
        _last_prefix = None
        _tab_count = 0
        return lcp

    
    if _last_prefix == text:
        _tab_count += 1
    else:
        _last_prefix = text
        _tab_count = 1

    if _tab_count == 1:
        sys.stdout.write("\x07")
        sys.stdout.flush()
        return None
    sys.stdout.write("\n" + "  ".join(matches) + "\n")
    sys.stdout.write("$ " + text)
    sys.stdout.flush()

    # Reset for next cycle
    _tab_count = 0
    return None 
 
def main():
    #these are the built-in commands
    builtin = ["exit", "echo", "type", "pwd", "cd"]
    #applying the loop condition
    readline.parse_and_bind("tab: complete") #binds the tab ket and complete the action automatically
    readline.set_completer(command_completer)
    while True:
        sys.stdout.write("$ ")

        #user takes the input
        command = input()

        #spliting the token 
        #e.g. echo 'hello world' yes
        tokens = shlex.split(command)

        redirect = False #means ki where the output should go (stdout)
        redirect_err = False # it is for the stderr output
        output_file = None #this is the output file 
        error_file = None #this is the error file 
        command_tokens = [] #this will only contains the commands only 
        append = False #this will not overwrite the files. It will add to the text

        if not tokens:
            continue
        
        command_tokens = tokens 
        
        for i, token in enumerate(tokens):
            if token == ">>" or token == "1>>":   
                append = True
                redirect  = True
                command_tokens = tokens[:i]  
                output_file = tokens[i + 1]
                break

            elif token.startswith(">>"): #he >> operator appends the standard output of a command to a file.
                redirect = True
                append = True
                command_tokens = tokens[:i]
                output_file = token[2:]
                break

            elif token == ">" or token == "1>": #The > operator redirects the standard output of a command to a file.
                redirect = True
                append = False
                command_tokens = tokens[:i]
                output_file = tokens[i+1]
                break

            elif token.startswith(">") and not token.startswith(">>"):
                redirect = True
                append = False
                command_tokens = tokens[:i]
                output_file = token[1:]      
                break
            
            elif token == "2>>": #The 2>> operator appends the standard error of a command to a file.
                redirect_err = True
                append = True
                command_tokens = tokens[:i]
                error_file = tokens[i + 1]
                break

            elif token.startswith("2>>"):
                redirect_err = True
                append = True
                command_tokens = tokens[:i]
                error_file = token[3:]
                break

            elif token == "2>": #The 2> operator redirects the standard error of a command to a file.
                redirect_err = True
                append = False
                command_tokens = tokens[:i]
                error_file = tokens[i + 1]
                break

            elif token.startswith("2>"):
                redirect_err = True
                append = False
                command_tokens = tokens[:i]
                error_file = token[2:]
                break
           
            else:
                command_tokens = tokens

        # exits the program 
        if command_tokens[0] == "exit":
            break

        # if we use the echo command it will print the comments
        elif command_tokens[0] == "echo":
            output = ""
            for i in range(1, len(command_tokens)):
                output += command_tokens[i] + " "
            output = output.rstrip() + "\n"

            if redirect:
                directory = os.path.dirname(output_file)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                mode = 'a' if append else "w"
                file = open(output_file, mode)
                file.write(output)
                file.close()
            else:
                sys.stdout.write(output)
            
            # create empty error file if redirected
            if redirect_err:
                directory = os.path.dirname(error_file)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                mode = 'a' if append else "w"
                open(error_file, mode).close()

        #the cd is used to change the directory 
        elif command_tokens[0] == "cd":
            try:
                 path = command_tokens[1]   #try to get the path if this fails then it will throw the error
            except IndexError:
                 sys.stdout.write("cd: missing argument\n")
                 continue
            #get back to the path
            path = os.path.expanduser(path)     
            try:
                 os.chdir(path)     # try to change directory
            except FileNotFoundError:
                 error_msg = f"cd: {path}: No such file or directory\n"
                 if redirect_err:
                     directory = os.path.dirname(error_file)
                     if directory:
                         os.makedirs(directory, exist_ok=True)
                     mode = "a" if append else "w" 
                     with open(error_file, mode) as file:
                         file.write(error_msg)
                 else:
                     sys.stdout.write(error_msg)
        
        #The pwd (print working directory) builtin prints the full, absolute path of the current working directory to stdout.
        elif command_tokens[0] == "pwd":
            output = os.getcwd() + "\n"
            if redirect:
                directory = os.path.dirname(output_file)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                mode = "a" if append else "w"
                with open(output_file, mode) as file:
                    file.write(output)
            else:
                sys.stdout.write(output)

            # create empty error file if redirected
            if redirect_err:
                directory = os.path.dirname(error_file)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                open(error_file, "w").close() 

        #this type command helps to find the path 
        elif command_tokens[0] == "type":
            output = ""
            if command_tokens[1] in builtin:
                output = command_tokens[1] + " is a shell builtin\n"
            elif path := shutil.which(command_tokens[1]):
                output = command_tokens[1] + " is " + path + "\n"
            else:
                output = command_tokens[1] + " not found\n"

            if redirect:
                directory = os.path.dirname(output_file)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                mode = "a" if append else "w"
                with open(output_file, mode) as file:
                    file.write(output)
            else:
                sys.stdout.write(output)

            # create empty error file if redirected
            if redirect_err:
                directory = os.path.dirname(error_file)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                mode = "a" if append else "w"
                open(error_file, mode).close()

        else:
            path = shutil.which(command_tokens[0])
            #this condition helps to run the program
            if path:
                if redirect:
                    directory = os.path.dirname(output_file) 
                    if directory:
                        os.makedirs(directory, exist_ok=True)
                    mode = "a" if append else "w"
                    file = open(output_file, mode)
                    subprocess.run(command_tokens, stdout=file)
                    file.close()
                elif redirect_err:
                    directory = os.path.dirname(error_file)
                    if directory:
                         os.makedirs(directory, exist_ok=True)
                    mode = "a" if append else "w"
                    file = open(error_file, mode)
                    subprocess.run(command_tokens, stderr=file)
                    file.close()
                else:
                    subprocess.run(command_tokens)
            else:        
                error_msg = command_tokens[0] + ": command not found\n"
                if redirect_err:
                    directory = os.path.dirname(error_file)
                    if directory:
                        os.makedirs(directory, exist_ok=True)
                    mode = "a" if append else "w"
                    with open(error_file, mode) as file:
                        file.write(error_msg)
                else:
                    sys.stdout.write(error_msg)

if __name__ == "__main__":
    main()
