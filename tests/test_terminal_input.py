#!/usr/bin/env python3
"""
Quick test to verify terminal input works correctly.
Run this before testing the main script.
"""

import asyncio
import concurrent.futures
from rich.console import Console

console = Console()

def test_basic_input():
    """Test 1: Basic input() function"""
    console.print("\n[bold]Test 1: Basic input()[/bold]")
    console.print("This tests if Python can read from your terminal.")
    try:
        response = input("Type something and press Enter: ")
        console.print(f"[green]✓ Success! You typed: '{response}'[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        return False

async def test_async_input():
    """Test 2: Async input with timeout (like the main script)"""
    console.print("\n[bold]Test 2: Async input with timeout[/bold]")
    console.print("This mimics how the main script handles input.")
    console.print("[yellow]You have 10 seconds to press Enter...[/yellow]")

    def wait_for_enter():
        try:
            input("\n[Press Enter to continue...] ")
            return True
        except (EOFError, KeyboardInterrupt):
            return False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(wait_for_enter)
        try:
            user_confirmed = await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=10.0
            )
            if user_confirmed:
                console.print("[green]✓ Success! Input received correctly[/green]")
                return True
            else:
                console.print("[yellow]⚠ Input was cancelled (EOFError or Ctrl+C)[/yellow]")
                return False
        except asyncio.TimeoutError:
            console.print("[yellow]⚠ Timeout - you didn't press Enter in time[/yellow]")
            return False

async def main():
    console.print("[bold cyan]Terminal Input Test[/bold cyan]")
    console.print("This will verify your terminal can handle interactive input.\n")

    # Test 1
    test1_passed = test_basic_input()

    if not test1_passed:
        console.print("\n[red]Basic input failed. Try using a different terminal (macOS Terminal app).[/red]")
        return

    # Test 2
    test2_passed = await test_async_input()

    # Summary
    console.print("\n" + "="*60)
    if test1_passed and test2_passed:
        console.print("[bold green]✓ All tests passed![/bold green]")
        console.print("Your terminal is ready to run the interactive basket analysis.")
        console.print("\nRun this command:")
        console.print("[cyan]python3 main.py --urls https://www.zooplus.co.uk/checkout/cart[/cyan]")
    else:
        console.print("[bold yellow]⚠ Some tests failed[/bold yellow]")
        console.print("\nTroubleshooting:")
        console.print("1. Use macOS Terminal app (not VS Code terminal)")
        console.print("2. Make sure you're not running in a restricted environment")
        console.print("3. Try automated mode instead:")
        console.print("   [cyan]python3 main.py --analysis-type homepage_pages --urls https://www.zooplus.co.uk[/cyan]")

if __name__ == "__main__":
    asyncio.run(main())
