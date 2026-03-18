import sys  #talks to the system
import shutil #file and program
import subprocess #run other porgrams
import os  #plays with the directory


def main():
    #these are the built-in commands
    builtin = ["exit", "echo", "type", "pwd", "cd"]
    #applying the loop condition
    while True:
        sys.stdout.write("$ ")

        #user takes the input
        command = input()

        #spliting the token 
        tokens = command.split(" ")
        # exits the program 
        if tokens[0] == "exit":
            break

        # if we use the echo command it will print the comments
        elif tokens[0] == "echo":
            for i in range(1, len(tokens)):
                sys.stdout.write(tokens[i] + " ")
            sys.stdout.write("\n")
        
        #the cd is used to change the directory 
        elif tokens[0] == "cd":
            try:
                 path = tokens[1]   #try to get the path if this fails then it will throw the error
            except IndexError:
                 sys.stdout.write("cd: missing argument\n")
                 continue
            path = os.path.expanduser(path)
            try:
                 os.chdir(path)     # try to change directory
            except FileNotFoundError:
                 sys.stdout.write(f"cd: {path}: No such file or directory\n")
        
        #The pwd (print working directory) builtin prints the full, absolute path of the current working directory to stdout.
        elif tokens[0] == "pwd":
            sys.stdout.write(os.getcwd() + "\n")

        #this type command helps to find the path 
        elif tokens[0] == "type":
            if tokens[1] in builtin:
                sys.stdout.write(tokens[1] + " is a shell builtin\n")
            elif path := shutil.which(tokens[1]):
                sys.stdout.write(tokens[1] + " is " + path + "\n")
            else:
                sys.stdout.write(tokens[1] + " not found\n")
        else:
            path = shutil.which(tokens[0])
            #this condition helps to run the program
            if path:
                    subprocess.run(tokens)
            else:        
                sys.stdout.write(tokens[0] + ": command not found\n")

if __name__ == "__main__":
    main()