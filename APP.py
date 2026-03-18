import sys  #talks to the system
import shutil #file and program
import subprocess #run other porgrams

def main():
    #these are the built-in commands
    builtin = ["exit", "echo", "type"]
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