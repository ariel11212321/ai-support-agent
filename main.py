import sys
from typing import List
from workflow import SupportWorkflow
from inputValidator import InputValidator
from config import Config
from worker_pool import WorkerPool



def process_question_worker(question_data, worker_id: int):
    """Worker function for processing questions in parallel"""
    question_text, show_details = question_data
    
    # Validate and sanitize input
    is_valid, error_msg = InputValidator.validate_question(question_text)
    if not is_valid:
        return {
            'worker_id': worker_id,
            'question': question_text,
            'error': f"Invalid input: {error_msg}",
            'success': False
        }
    
    sanitized_question = InputValidator.sanitize_input(question_text)
    
    try:
        workflow = SupportWorkflow()
        result = workflow.process(sanitized_question)
        
        # Extract result data
        response_data = {
            'worker_id': worker_id,
            'question': sanitized_question,
            'success': True,
            'ticket_id': result.ticket_id,
            'category': result.classification.category.value if result.classification else 'unknown',
            'confidence': result.classification.confidence if result.classification else 0.0,
            'response_message': result.response.message if result.response else 'No response generated',
            'escalated': result.requires_escalation,
            'error': result.error,
            'errors': result.errors,
            'warnings': result.warnings
        }
        
        if result.escalation_info:
            response_data['escalation_reason'] = result.escalation_info.get('reason', 'Unknown')
            response_data['escalation_department'] = result.escalation_info.get('department', 'General')
        
        if show_details and result.processing_metrics:
            response_data['processing_time_ms'] = result.processing_metrics.get('total_time_ms', 0)
            response_data['api_calls'] = result.processing_metrics.get('api_calls', 0)
        
        return response_data
        
    except Exception as e:
        return {
            'worker_id': worker_id,
            'question': sanitized_question,
            'error': f"Unexpected error: {str(e)}",
            'success': False
        }


def process_single_question(question_text: str, show_details: bool = False):
    result = process_question_worker((question_text, show_details), 0)
    display_result(result, show_details)


def process_batch_questions(questions: List[str], show_details: bool = False):
    print(f"\n🔄 Processing {len(questions)} questions in parallel...")
    print("=" * 60)
    
    # Prepare question data
    question_data = [(q, show_details) for q in questions]
    
    # Process in parallel
    worker_pool = WorkerPool()
    results = worker_pool.process_batch(question_data, process_question_worker)
    
    # Sort results by worker_id to maintain order
    results.sort(key=lambda x: x['worker_id'])
    
    # Display results
    successful = 0
    failed = 0
    escalated = 0
    
    for i, result in enumerate(results, 1):
        print(f"\n📋 Question {i}:")
        display_result(result, show_details)
        
        if result['success']:
            successful += 1
            if result.get('escalated', False):
                escalated += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n📊 Batch Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   🚨 Escalated: {escalated}")
    print(f"   📈 Success Rate: {(successful/len(questions)*100):.1f}%")


def display_result(result: dict, show_details: bool = False):
    """Display a single result in a formatted way"""
    if not result['success']:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"💬 Question: {result['question']}")
    print(f"📂 Category: {result['category'].title()} ({result['confidence']:.1%})")
    
    # Check if escalated
    if result.get('escalated', False):
        print(f"🚨 ESCALATED: {result['response_message']}")
        if 'escalation_reason' in result:
            print(f"   Reason: {result['escalation_reason']}")
            print(f"   Department: {result['escalation_department']}")
    else:
        print(f"🤖 Response: {result['response_message']}")
    
    if show_details:
        if 'processing_time_ms' in result:
            print(f"⏱️ Processing time: {result['processing_time_ms']:.1f}ms")
            print(f"🔧 API calls: {result.get('api_calls', 0)}")
        
        if result.get('warnings'):
            print(f"⚠️ Warnings: {len(result['warnings'])}")
            for warning in result['warnings'][:3]:  # Show first 3 warnings
                print(f"   - {warning}")
        
        if result.get('ticket_id'):
            print(f"🎫 Ticket ID: {result['ticket_id']}")


def interactive_mode():
    """Interactive AI-powered question-answer mode with input validation"""
    try:
        workflow = SupportWorkflow()
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {str(e)}")
        return
    
    print("🤖 AI Support System - Interactive Mode")
    print("Type 'quit', 'exit', or 'q' to exit")
    print("Type 'help' for usage information")
    print("Type 'batch' to enter batch processing mode\n")
    
    while True:
        try:
            question = input("Ask your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if question.lower() == 'help':
                print("\n📖 Help:")
                print("- Ask any support question")
                print("- Questions must be 3-5000 characters long")
                print("- Avoid special characters and code")
                print("- Type 'batch' for batch processing mode")
                print("- Type 'quit' to exit\n")
                continue
            
            if question.lower() == 'batch':
                batch_interactive_mode()
                continue
            
            if not question:
                print("⚠️ Please enter a question")
                continue
            
            # Validate input
            is_valid, error_msg = InputValidator.validate_question(question)
            if not is_valid:
                print(f"❌ Invalid input: {error_msg}")
                continue
            
            # Sanitize and process
            sanitized_question = InputValidator.sanitize_input(question)
            print("\n🔄 Processing...")
            
            result = workflow.process(sanitized_question)
            if result.error:
                print(f"❌ Error: {result.error}")
            else:
                print(f"\n📂 {result.classification.category.value.title()} ({result.classification.confidence:.1%})")
                print(f"🤖 {result.response.message}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
    
    print("👋 Goodbye!")


def batch_interactive_mode():
    """Interactive batch processing mode"""
    print("\n🔄 Batch Processing Mode")
    print("Enter questions one by one. Type 'done' when finished.")
    print("Type 'cancel' to return to main mode.\n")
    
    questions = []
    
    while True:
        try:
            question = input(f"Question {len(questions) + 1}: ").strip()
            
            if question.lower() == 'done':
                if questions:
                    show_details = input("Show detailed results? (y/n): ").lower().startswith('y')
                    process_batch_questions(questions, show_details)
                else:
                    print("⚠️ No questions entered.")
                break
            
            if question.lower() == 'cancel':
                print("🚫 Batch processing cancelled.")
                break
            
            if not question:
                print("⚠️ Please enter a question")
                continue
            
            # Validate input
            is_valid, error_msg = InputValidator.validate_question(question)
            if not is_valid:
                print(f"❌ Invalid input: {error_msg}")
                continue
            
            questions.append(question)
            print(f"✅ Added question {len(questions)}")
        
        except KeyboardInterrupt:
            print("\n🚫 Batch processing interrupted.")
            break


def main():
    """Main CLI function with comprehensive input validation and batch processing"""
    args = sys.argv[1:]
    
    # Validate command line arguments
    is_valid_args, args_error = InputValidator.validate_command_args(args)
    if not is_valid_args:
        print(f"❌ Invalid command line arguments: {args_error}")
        return
    
    if not args:
        interactive_mode()
        return
    
    if "-q" in args:
        try:
            idx = args.index("-q")
            if idx + 1 < len(args):
                question = args[idx + 1]
                show_details = "-d" in args
                process_single_question(question, show_details)
            else:
                print("❌ Please provide a question after -q")
        except (ValueError, IndexError) as e:
            print(f"❌ Error parsing arguments: {str(e)}")
    
    elif "-batch" in args:
        try:
            idx = args.index("-batch")
            if idx + 1 < len(args):
                # Expect comma-separated questions
                questions_str = args[idx + 1]
                questions = [q.strip() for q in questions_str.split(',') if q.strip()]
                if questions:
                    show_details = "-d" in args
                    process_batch_questions(questions, show_details)
                else:
                    print("❌ No valid questions found in batch")
            else:
                print("❌ Please provide comma-separated questions after -batch")
        except (ValueError, IndexError) as e:
            print(f"❌ Error parsing batch arguments: {str(e)}")
    
    else:
        print("📖 Usage:")
        print("  python main.py                              # Interactive AI mode")
        print("  python main.py -q 'question'                # Single question")
        print("  python main.py -q 'question' -d             # Single question with details")
        print("  python main.py -batch 'q1,q2,q3'           # Batch processing")
        print("  python main.py -batch 'q1,q2,q3' -d        # Batch processing with details")
        print("\n🛡️ Input Requirements:")
        print(f"  - Questions: {InputValidator.MIN_QUESTION_LENGTH}-{InputValidator.MAX_QUESTION_LENGTH} characters")
        print("  - No code injection or suspicious patterns")
        print("  - Standard text characters only")
        print(f"\n⚡ Performance:")
        print(f"  - Parallel processing with up to {Config.MAX_WORKERS} workers")
        print("  - Batch mode for processing multiple questions efficiently")


if __name__ == "__main__":
    main()