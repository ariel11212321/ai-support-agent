import sys
import json
from pathlib import Path
from workflow import SupportWorkflow
from worker_pool import WorkerPool

def process_single_question(question_text: str, show_details: bool = False):
    """Process a single question with AI"""
    print(f"\n💬 Question: {question_text}")
    print("=" * 50)
    
    workflow = SupportWorkflow()
    result = workflow.process(question_text)
    
    if result.error:
        print(f"❌ Error: {result.error}")
        return
    
    print(f"\n📂 Category: {result.classification.category.value.title()}")
    print(f"🎯 Confidence: {result.classification.confidence:.1%}")
    print(f"\n🤖 AI Response:")
    print(f"💡 {result.response.message}")
    
    if show_details:
        print(f"\n⏱️  Total Processing Time: {result.response.processing_time_ms:.1f}ms")
        if result.classification.worker_id is not None:
            print(f"👷 Worker ID: {result.classification.worker_id}")

def interactive_mode():
    """Interactive AI-powered question-answer mode"""
    workflow = SupportWorkflow()
    print("\n🤖 AI Support Agent - Powered by HuggingFace")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            question = input("Ask your question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if question:
                print("\n🔄 Processing...")
                result = workflow.process(question)
                if result.error:
                    print(f"❌ Error: {result.error}")
                else:
                    print(f"\n📂 {result.classification.category.value.title()} ({result.classification.confidence:.1%})")
                    print(f"🤖 {result.response.message}\n")
        
        except KeyboardInterrupt:
            break
    
    print("👋 Goodbye!")

def main():
    """Main CLI function"""
    args = sys.argv[1:]
    
    if not args:
        interactive_mode()
        return
    
    if "-q" in args:
        idx = args.index("-q")
        if idx + 1 < len(args):
            question = args[idx + 1]
            show_details = "-d" in args
            process_single_question(question, show_details)
        else:
            print("❌ Please provide a question after -q")
    else:
        print("Usage:")
        print("  python main.py                    # Interactive AI mode")
        print("  python main.py -q 'question' -d   # Single question with details")

if __name__ == "__main__":
    main()