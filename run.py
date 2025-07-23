import subprocess
import sys

def main():
    """Quick launcher for the AI Support Agent"""
    print("🚀 AI Support Agent Launcher")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        
        subprocess.run([sys.executable, "main.py"] + sys.argv[1:])
    else:
       
        print("1. Interactive Mode")
        print("2. Test Single Question")
        print("3. Test Batch Processing")
        print("4. Custom Command")
        
        choice = input("\nChoose option (1-4): ").strip()
        
        if choice == "1":
            subprocess.run([sys.executable, "main.py"])
        elif choice == "2":
            question = input("Enter your question: ")
            subprocess.run([sys.argv[0], "main.py", "-q", question, "-d"])
        elif choice == "3":
            subprocess.run([sys.argv[0], "main.py", "-f", "test_questions.txt"])
        elif choice == "4":
            command = input("Enter command: ")
            subprocess.run([sys.argv[0], "main.py"] + command.split())

if __name__ == "__main__":
    main()