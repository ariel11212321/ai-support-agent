"""
AI Support Agent - Main CLI Interface
Beautiful, interactive command-line interface with Rich formatting
"""

import argparse
import sys
import time
import uuid
from datetime import datetime
from typing import List, Optional

# Rich imports for beautiful CLI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align

# Application imports
from models import UserQuestion, ConversationHistory
from workflow import SupportWorkflow
from worker_pool import WorkerPool
from cache import ResponseCache
from analytics import AnalyticsEngine
from storage import DataStorage
from config import Config, Colors


class SupportAgentCLI:
    """
    Main CLI application for the AI Support Agent
    Provides interactive and batch processing modes with beautiful output
    """
    
    def __init__(self):
        """Initialize CLI application"""
        self.console = Console()
        
        # Initialize core components
        self.workflow = SupportWorkflow()
        self.worker_pool = WorkerPool()
        self.cache = ResponseCache()
        self.analytics = AnalyticsEngine()
        self.storage = DataStorage()
        
        # Session management
        self.current_session_id = str(uuid.uuid4())
        self.conversation_history = ConversationHistory(session_id=self.current_session_id)
        
        # Application state
        self.running = True
        self.stats_enabled = True
    
    def run(self, args: Optional[argparse.Namespace] = None) -> None:
        """
        Main entry point for CLI application
        
        Args:
            args: Parsed command line arguments
        """
        try:
            # Display welcome message
            self._display_welcome()
            
            # Handle different modes based on arguments
            if args and args.question:
                self._single_question_mode(args.question, args.details)
            elif args and args.batch_file:
                self._batch_mode(args.batch_file, args.output)
            elif args and args.analytics:
                self._analytics_mode()
            else:
                self._interactive_mode()
                
        except KeyboardInterrupt:
            self._display_goodbye()
        except Exception as e:
            self.console.print(f"[red]❌ Unexpected error: {e}[/red]")
        finally:
            self._cleanup()
    
    def _display_welcome(self) -> None:
        """Display welcome message with system status"""
        # Create welcome panel
        welcome_text = f"""
[bold green]{Config.APP_NAME} v{Config.APP_VERSION}[/bold green]
[cyan]{Config.APP_DESCRIPTION}[/cyan]

🤖 [bold]System Status:[/bold] Ready
⚡ [bold]Workers:[/bold] {self.worker_pool.max_workers} active
💾 [bold]Cache:[/bold] Ready (Size: {len(self.cache)})
📊 [bold]Analytics:[/bold] Tracking enabled
        """.strip()
        
        welcome_panel = Panel(
            welcome_text,
            title="🚀 Welcome",
            border_style="bright_green",
            padding=(1, 2)
        )
        
        self.console.print(welcome_panel)
        self.console.print()
        
        # Display quick stats
        self._display_quick_stats()
    
    def _display_quick_stats(self) -> None:
        """Display quick system statistics"""
        # Get current stats
        worker_stats = self.worker_pool.get_performance_stats()
        cache_stats = self.cache.get_stats()
        
        # Create stats table
        stats_table = Table(show_header=False, box=None, padding=(0, 1))
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="bright_white")
        
        stats_table.add_row("🔥 Total Questions Processed", str(worker_stats["total_tasks_processed"]))
        stats_table.add_row("⚡ Avg Response Time", f"{worker_stats['average_processing_time_ms']:.1f}ms")
        stats_table.add_row("🎯 Cache Hit Rate", f"{cache_stats['hit_rate_percent']:.1f}%")
        stats_table.add_row("🕐 Uptime", f"{worker_stats['uptime_seconds'] / 3600:.1f}h")
        
        self.console.print(Align.center(stats_table))
        self.console.print()
    
    def _interactive_mode(self) -> None:
        """Run in interactive chat mode"""
        self.console.print(Panel(
            "[bold cyan]Interactive Mode[/bold cyan]\n"
            "Type your questions below. Commands:\n"
            "• [yellow]stats[/yellow] - Show detailed statistics\n"
            "• [yellow]clear[/yellow] - Clear screen\n"
            "• [yellow]history[/yellow] - Show conversation history\n"
            "• [yellow]help[/yellow] - Show help\n"
            "• [yellow]quit[/yellow] - Exit application",
            title="💬 Chat Mode",
            border_style="blue"
        ))
        
        while self.running:
            try:
                # Get user input with rich prompt
                question = Prompt.ask(
                    f"\n[{Colors.PROMPT_COLOR}]{Config.CLI_PROMPT}[/{Colors.PROMPT_COLOR}]",
                    default=""
                )
                
                if not question.strip():
                    continue
                
                # Handle commands
                if question.lower() in ['quit', 'exit', 'bye']:
                    break
                elif question.lower() == 'stats':
                    self._show_detailed_stats()
                    continue
                elif question.lower() == 'clear':
                    self.console.clear()
                    self._display_welcome()
                    continue
                elif question.lower() == 'history':
                    self._show_conversation_history()
                    continue
                elif question.lower() == 'help':
                    self._show_help()
                    continue
                
                # Process question
                self._process_question_interactive(question)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        self._display_goodbye()
    
    def _process_question_interactive(self, question_text: str) -> None:
        """Process a question in interactive mode with live updates"""
        # Create user question
        user_question = UserQuestion(
            text=question_text,
            user_id="cli_user",
            session_id=self.current_session_id
        )
        
        # Check cache first
        cached_response = self.cache.get(user_question)
        if cached_response:
            self._display_response(cached_response, from_cache=True)
            return
        
        # Process with live progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        ) as progress:
            
            task = progress.add_task("🤔 Processing your question...", total=100)
            
            # Submit to worker pool
            start_time = time.time()
            
            # Simulate processing steps with progress updates
            progress.update(task, advance=20, description="🤔 Analyzing question...")
            time.sleep(0.1)
            
            progress.update(task, advance=30, description="🧠 Classifying category...")
            time.sleep(0.1)
            
            progress.update(task, advance=25, description="⚡ Generating response...")
            
            # Actually process the question
            result = self.workflow.process_question(user_question, worker_id=1)
            
            progress.update(task, advance=25, description="✅ Complete!")
            time.sleep(0.1)
        
        # Display results
        if result.get("error"):
            self.console.print(f"[red]❌ Error: {result['error']}[/red]")
            return
        
        response_data = result.get("final_response")
        if response_data:
            from models import SupportResponse
            response = SupportResponse(**response_data)
            
            # Cache the response
            self.cache.put(user_question, response)
            
            # Record analytics
            if result.get("classification"):
                from models import ClassificationResult
                classification = ClassificationResult(**result["classification"])
                self.analytics.record_interaction(user_question, classification, response)
            
            # Add to conversation history
            self.conversation_history.add_exchange(user_question, response)
            
            # Display response
            self._display_response(response, processing_time=time.time() - start_time)
    
    def _display_response(self, response, from_cache: bool = False, processing_time: float = None) -> None:
        """Display a formatted response"""
        # Category color mapping
        category_colors = {
            "billing": Colors.BILLING_COLOR,
            "technical": Colors.TECHNICAL_COLOR,
            "general": Colors.GENERAL_COLOR
        }
        
        category_color = category_colors.get(response.category.value, "white")
        
        # Create main response panel
        response_content = f"""
[bold {category_color}]📂 Category:[/bold {category_color}] {response.category.value.title()}
[bold]🎯 Confidence:[/bold] {response.confidence:.1%}
        """
        
        if from_cache:
            response_content += "[bold yellow]⚡ From Cache[/bold yellow]\n"
        elif processing_time:
            response_content += f"[bold]⏱️  Processing Time:[/bold] {processing_time*1000:.1f}ms\n"
        
        response_content += f"\n[bold green]💬 Response:[/bold green]\n{response.response}"
        
        response_panel = Panel(
            response_content,
            title="🤖 AI Support Response",
            border_style=category_color,
            padding=(1, 2)
        )
        
        self.console.print(response_panel)
        
        # Display suggested actions if available
        if response.suggested_actions:
            actions_table = Table(title="📋 Suggested Actions", show_header=False, box=None)
            actions_table.add_column("", style="cyan", width=3)
            actions_table.add_column("Action", style="white")
            
            for i, action in enumerate(response.suggested_actions, 1):
                actions_table.add_row(f"{i}.", action)
            
            self.console.print(actions_table)
        
        # Display escalation warning if needed
        if response.escalation_needed:
            escalation_panel = Panel(
                "[bold yellow]⚠️  This issue may require human assistance[/bold yellow]\n"
                f"Priority: [bold]{response.priority.value.upper()}[/bold]",
                border_style="yellow",
                padding=(0, 2)
            )
            self.console.print(escalation_panel)
        
        self.console.print("─" * 60)
    
    def _single_question_mode(self, question: str, show_details: bool = False) -> None:
        """Process a single question and display results"""
        self.console.print(f"[cyan]Processing:[/cyan] {question}")
        self.console.print()
        
        # Create user question
        user_question = UserQuestion(text=question, user_id="cli_user")
        
        # Process question
        start_time = time.time()
        result = self.workflow.process_question(user_question)
        processing_time = time.time() - start_time
        
        # Display results
        if result.get("error"):
            self.console.print(f"[red]❌ Error: {result['error']}[/red]")
            return
        
        response_data = result.get("final_response")
        classification_data = result.get("classification")
        
        if response_data:
            from models import SupportResponse, ClassificationResult
            response = SupportResponse(**response_data)
            
            if show_details and classification_data:
                classification = ClassificationResult(**classification_data)
                self._display_detailed_classification(classification)
            
            self._display_response(response, processing_time=processing_time)
    
    def _display_detailed_classification(self, classification) -> None:
        """Display detailed classification information"""
        details_table = Table(title="🔍 Classification Details", show_header=False)
        details_table.add_column("Property", style="cyan")
        details_table.add_column("Value", style="white")
        
        details_table.add_row("Category", classification.category.value.title())
        details_table.add_row("Confidence", f"{classification.confidence:.2%}")
        details_table.add_row("Processing Time", f"{classification.processing_time_ms:.1f}ms")
        details_table.add_row("Features Detected", ", ".join(classification.features_detected))
        details_table.add_row("Reasoning", classification.reasoning)
        
        if classification.worker_id:
            details_table.add_row("Worker ID", str(classification.worker_id))
        
        self.console.print(details_table)
        self.console.print()
    
    def _batch_mode(self, batch_file: str, output_file: Optional[str] = None) -> None:
        """Process questions from a batch file"""
        try:
            # Read questions from file
            with open(batch_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
            
            if not questions:
                self.console.print("[red]❌ No questions found in batch file[/red]")
                return
            
            self.console.print(f"[cyan]📁 Processing {len(questions)} questions from {batch_file}[/cyan]")
            self.console.print()
            
            # Process questions with progress bar
            results = []
            
            with Progress(
                TextColumn("[progress.description]"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TextColumn("{task.completed}/{task.total} questions"),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                
                task = progress.add_task("Processing questions...", total=len(questions))
                
                for i, question_text in enumerate(questions):
                    user_question = UserQuestion(text=question_text, user_id=f"batch_user_{i}")
                    
                    # Process question
                    result = self.workflow.process_question(user_question)
                    results.append({
                        "question": question_text,
                        "result": result
                    })
                    
                    progress.update(task, advance=1)
            
            # Display summary
            self._display_batch_summary(results)
            
            # Save results if output file specified
            if output_file:
                self._save_batch_results(results, output_file)
                
        except FileNotFoundError:
            self.console.print(f"[red]❌ File not found: {batch_file}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Error processing batch file: {e}[/red]")
    
    def _display_batch_summary(self, results: List[dict]) -> None:
        """Display summary of batch processing results"""
        # Calculate summary statistics
        total_questions = len(results)
        successful = sum(1 for r in results if not r["result"].get("error"))
        failed = total_questions - successful
        
        # Category distribution
        categories = {}
        avg_confidence = 0
        confidence_count = 0
        
        for result in results:
            if not result["result"].get("error"):
                response_data = result["result"].get("final_response", {})
                category = response_data.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1
                
                if "classification" in result["result"]:
                    confidence = result["result"]["classification"].get("confidence", 0)
                    avg_confidence += confidence
                    confidence_count += 1
        
        if confidence_count > 0:
            avg_confidence /= confidence_count
        
        # Create summary table
        summary_table = Table(title="📊 Batch Processing Summary", show_header=True)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Total Questions", str(total_questions))
        summary_table.add_row("Successful", f"[green]{successful}[/green]")
        summary_table.add_row("Failed", f"[red]{failed}[/red]" if failed > 0 else "0")
        summary_table.add_row("Success Rate", f"{successful/total_questions*100:.1f}%")
        summary_table.add_row("Avg Confidence", f"{avg_confidence:.1%}")
        
        self.console.print(summary_table)
        
        # Category distribution
        if categories:
            self.console.print("\n[bold]📂 Category Distribution:[/bold]")
            for category, count in categories.items():
                percentage = count / successful * 100 if successful > 0 else 0
                self.console.print(f"  • {category.title()}: {count} ({percentage:.1f}%)")
    
    def _save_batch_results(self, results: List[dict], output_file: str) -> None:
        """Save batch processing results to file"""
        try:
            import json
            
            output_data = {
                "processed_at": datetime.now().isoformat(),
                "total_questions": len(results),
                "results": results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            self.console.print(f"\n[green]✅ Results saved to {output_file}[/green]")
            
        except Exception as e:
            self.console.print(f"\n[red]❌ Error saving results: {e}[/red]")
    
    def _analytics_mode(self) -> None:
        """Display comprehensive analytics dashboard"""
        self.console.clear()
        
        # Get analytics data
        dashboard_metrics = self.analytics.get_dashboard_metrics()
        performance_insights = self.analytics.get_performance_insights()
        cache_stats = self.cache.get_stats()
        worker_stats = self.worker_pool.get_performance_stats()
        
        # Create analytics layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Header
        header_text = Text(f"📊 {Config.APP_NAME} - Analytics Dashboard", style="bold bright_green")
        layout["header"] = Panel(Align.center(header_text), border_style="bright_green")
        
        # Left panel - Overview
        overview_table = Table(title="📈 Overview", show_header=False)
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="bright_white")
        
        overview = dashboard_metrics.get("overview", {})
        overview_table.add_row("Total Questions", str(overview.get("total_questions", 0)))
        overview_table.add_row("Questions/Hour", f"{overview.get('questions_per_hour', 0):.1f}")
        overview_table.add_row("Avg Confidence", f"{overview.get('average_confidence', 0):.1f}%")
        overview_table.add_row("Avg Response Time", f"{overview.get('average_response_time_ms', 0):.1f}ms")
        overview_table.add_row("Uptime", f"{overview.get('uptime_hours', 0):.1f}h")
        
        layout["left"] = Panel(overview_table, border_style="blue")
        
        # Right panel - System Stats
        system_table = Table(title="⚙️ System Performance", show_header=False)
        system_table.add_column("Component", style="cyan")
        system_table.add_column("Status", style="bright_white")
        
        system_table.add_row("Workers", f"{worker_stats.get('worker_count', 0)} active")
        system_table.add_row("Cache Hit Rate", f"{cache_stats.get('hit_rate_percent', 0):.1f}%")
        system_table.add_row("Cache Size", f"{cache_stats.get('cache_size', 0)}/{cache_stats.get('max_size', 0)}")
        system_table.add_row("Active Tasks", str(worker_stats.get('active_tasks', 0)))
        
        layout["right"] = Panel(system_table, border_style="magenta")
        
        # Display the layout
        self.console.print(layout)
        
        # Category distribution
        categories = dashboard_metrics.get("categories", {})
        if categories:
            self.console.print("\n[bold]📂 Category Distribution:[/bold]")
            cat_table = Table(show_header=True)
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Percentage", style="bright_white")
            cat_table.add_column("Bar", style="green")
            
            for category, percentage in categories.items():
                bar_length = int(percentage / 5)  # Scale for display
                bar = "█" * bar_length + "░" * (20 - bar_length)
                cat_table.add_row(category.title(), f"{percentage:.1f}%", bar)
            
            self.console.print(cat_table)
        
        # Performance insights
        insights = performance_insights.get("recommendations", [])
        if insights:
            self.console.print("\n[bold]💡 Recommendations:[/bold]")
            for i, insight in enumerate(insights, 1):
                self.console.print(f"  {i}. {insight}")
        
        self.console.print("\n[dim]Press any key to continue...[/dim]")
        input()
    
    def _show_detailed_stats(self) -> None:
        """Show detailed statistics in interactive mode"""
        self.console.print()
        
        # Get all stats
        cache_stats = self.cache.get_stats()
        worker_stats = self.worker_pool.get_performance_stats()
        dashboard_metrics = self.analytics.get_dashboard_metrics()
        
        # Performance stats table
        perf_table = Table(title="⚡ Performance Statistics", show_header=True)
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="bright_white")
        perf_table.add_column("Status", style="green")
        
        # Add performance rows
        avg_time = worker_stats.get('average_processing_time_ms', 0)
        time_status = "🚀 Excellent" if avg_time < 50 else "✅ Good" if avg_time < 100 else "⚠️ Slow"
        
        hit_rate = cache_stats.get('hit_rate_percent', 0)
        cache_status = "🚀 Excellent" if hit_rate > 80 else "✅ Good" if hit_rate > 50 else "⚠️ Low"
        
        perf_table.add_row("Avg Response Time", f"{avg_time:.1f}ms", time_status)
        perf_table.add_row("Cache Hit Rate", f"{hit_rate:.1f}%", cache_status)
        perf_table.add_row("Total Processed", str(worker_stats.get('total_tasks_processed', 0)), "📊")
        perf_table.add_row("Active Workers", str(worker_stats.get('worker_count', 0)), "👷")
        
        self.console.print(perf_table)
        
        # Cache details
        if cache_stats.get('cache_size', 0) > 0:
            self.console.print(f"\n[bold]💾 Cache Details:[/bold]")
            self.console.print(f"  • Size: {cache_stats['cache_size']}/{cache_stats['max_size']} entries")
            self.console.print(f"  • Utilization: {cache_stats['utilization_percent']:.1f}%")
            self.console.print(f"  • Total Requests: {cache_stats['total_requests']}")
            self.console.print(f"  • Hits: {cache_stats['hits']} | Misses: {cache_stats['misses']}")
        
        self.console.print()
    
    def _show_conversation_history(self) -> None:
        """Show current conversation history"""
        if not self.conversation_history.questions:
            self.console.print("[yellow]No conversation history yet.[/yellow]")
            return
        
        self.console.print(f"\n[bold]📜 Conversation History (Session: {self.current_session_id[:8]}...)[/bold]")
        
        for i, (question, response) in enumerate(zip(
            self.conversation_history.questions,
            self.conversation_history.responses
        ), 1):
            # Question
            self.console.print(f"\n[cyan]Q{i}:[/cyan] {question.text}")
            
            # Response summary
            category_color = {
                "billing": "yellow",
                "technical": "red", 
                "general": "blue"
            }.get(response.category.value, "white")
            
            self.console.print(f"[{category_color}]A{i}:[/{category_color}] {response.response[:100]}...")
            self.console.print(f"     [dim]Category: {response.category.value} | Confidence: {response.confidence:.1%}[/dim]")
        
        self.console.print()
    
    def _show_help(self) -> None:
        """Display help information"""
        help_panel = Panel(
            """[bold cyan]AI Support Agent Help[/bold cyan]

[bold]Interactive Commands:[/bold]
• [yellow]stats[/yellow]   - Show detailed performance statistics
• [yellow]clear[/yellow]   - Clear the screen and refresh
• [yellow]history[/yellow] - Show conversation history for this session
• [yellow]help[/yellow]    - Show this help message
• [yellow]quit[/yellow]    - Exit the application

[bold]Question Types:[/bold]
• [yellow]Billing[/yellow]   - Payment, subscriptions, refunds, pricing
• [yellow]Technical[/yellow] - Server issues, APIs, errors, performance
• [yellow]General[/yellow]   - How-to questions, features, documentation

[bold]Tips:[/bold]
• Be specific in your questions for better classification
• Questions are cached for faster repeated responses
• All interactions are tracked for analytics

[bold]Examples:[/bold]
• "How do I cancel my subscription?"
• "My server is returning 500 errors"
• "What features are available in the premium plan?"
            """,
            title="❓ Help",
            border_style="bright_blue",
            padding=(1, 2)
        )
        
        self.console.print(help_panel)
    
    def _display_goodbye(self) -> None:
        """Display goodbye message with session summary"""
        # Save conversation history
        if self.conversation_history.total_exchanges > 0:
            self.storage.save_conversation(self.conversation_history)
        
        # Session summary
        exchanges = self.conversation_history.total_exchanges
        
        goodbye_text = f"""[bold green]Thank you for using {Config.APP_NAME}![/bold green]

[bold]Session Summary:[/bold]
• Questions Asked: {exchanges}
• Session ID: {self.current_session_id[:8]}...
• Data Saved: {'✅ Yes' if exchanges > 0 else '❌ No'}

[cyan]Your conversation has been saved for future reference.[/cyan]
[dim]Have a great day! 👋[/dim]"""
        
        goodbye_panel = Panel(
            goodbye_text,
            title="👋 Goodbye",
            border_style="bright_green",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(goodbye_panel)
    
    def _cleanup(self) -> None:
        """Cleanup resources before exit"""
        try:
            # Save analytics
            self.storage.save_analytics(self.analytics.analytics_data)
            
            # Save cache data
            cache_data = self.cache.export_cache_data()
            self.storage.save_cache_data(cache_data)
            
            # Shutdown worker pool
            self.worker_pool.shutdown(wait=True, timeout=5)
            
        except Exception as e:
            self.console.print(f"[dim red]Warning: Cleanup error: {e}[/dim red]")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description=f"{Config.APP_NAME} - {Config.APP_DESCRIPTION}",
        epilog="Examples:\n"
               "  python main.py                                    # Interactive mode\n"
               "  python main.py -q \"My server is down!\" -d        # Single question with details\n"
               "  python main.py -b questions.txt -o results.json  # Batch processing\n"
               "  python main.py --analytics                       # Analytics dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Execution modes
    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        "-q", "--question",
        type=str,
        help="Process a single question and exit"
    )
    
    mode_group.add_argument(
        "-b", "--batch-file",
        type=str,
        help="Process questions from a file (one per line)"
    )
    
    mode_group.add_argument(
        "--analytics",
        action="store_true",
        help="Show analytics dashboard and exit"
    )
    
    # Options
    parser.add_argument(
        "-d", "--details",
        action="store_true",
        help="Show detailed classification information"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file for batch processing results (JSON format)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"{Config.APP_NAME} v{Config.APP_VERSION}"
    )
    
    return parser


def main() -> None:
    """Main entry point"""
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if args.batch_file and not args.batch_file.endswith(('.txt', '.csv')):
        print("Error: Batch file must be a .txt or .csv file")
        sys.exit(1)
    
    if args.output and not args.output.endswith('.json'):
        print("Error: Output file must be a .json file")
        sys.exit(1)
    
    # Create and run CLI application
    try:
        app = SupportAgentCLI()
        app.run(args)
    except Exception as e:
        console = Console()
        console.print(f"[red]💥 Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()