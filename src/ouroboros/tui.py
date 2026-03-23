"""
Ouroboros TUI - Self-Prompting AI Terminal Interface

A terminal UI where the AI prompts itself continuously while allowing
user intervention at any time.

Event handling strategy:
- Uses threading to separate display from AI processing
- Non-blocking input with select() on unix
- User can interrupt, redirect, or pause the autonomous loop
"""

import sys
import os
import threading
import time
import select
import tty
import termios
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
from queue import Queue, Empty


class LoopState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class TUIState:
    """State for the TUI."""
    loop_state: LoopState = LoopState.STOPPED
    current_focus: str = "Initializing..."
    last_prompt: str = ""
    last_result: str = ""
    iterations: int = 0
    insights: list = field(default_factory=list)
    log_messages: list = field(default_factory=list)

    def add_log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {msg}")
        # Keep last 100 messages
        if len(self.log_messages) > 100:
            self.log_messages = self.log_messages[-100:]


class OuroborosTUI:
    """
    Terminal UI for the self-prompting AI loop.

    Features:
    - Autonomous self-prompting in background thread
    - Non-blocking keyboard input
    - User can pause/resume/redirect at any time
    - Persistent display of state and history
    """

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(exist_ok=True)

        # Import here to avoid circular imports
        from .core.self_prompt_loop import SelfPrompter
        self.prompter = SelfPrompter(state_dir / "self_prompt_state.json")

        self.tui_state = TUIState()
        self.input_queue = Queue()
        self.running = True

        # Terminal state
        self.old_settings = None
        self.rows = 24
        self.cols = 80

    def get_terminal_size(self):
        try:
            self.rows, self.cols = os.get_terminal_size()
        except:
            self.rows, self.cols = 24, 80

    def clear(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def move_cursor(self, row: int, col: int):
        sys.stdout.write(f"\033[{row};{col}H")
        sys.stdout.flush()

    def hide_cursor(self):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def show_cursor(self):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def set_color(self, color: str):
        colors = {
            "reset": "\033[0m",
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "dim": "\033[2m",
            "bold": "\033[1m",
        }
        sys.stdout.write(colors.get(color, ""))
        sys.stdout.flush()

    def draw_frame(self):
        """Draw the TUI frame."""
        self.get_terminal_size()
        self.clear()

        # Header
        self.move_cursor(1, 1)
        self.set_color("cyan")
        print("═" * self.cols)
        self.set_color("bold")
        print("  🐍 OUROBOROS - Self-Prompting AI Loop")
        self.set_color("reset")
        self.set_color("cyan")
        print("═" * self.cols)
        self.set_color("reset")

        # Status line
        print()
        state_color = {
            LoopState.RUNNING: "green",
            LoopState.PAUSED: "yellow",
            LoopState.STOPPED: "red",
        }
        self.set_color(state_color.get(self.tui_state.loop_state, "white"))
        print(f"  State: {self.tui_state.loop_state.value.upper()}")
        self.set_color("reset")
        print(f"  Focus: {self.tui_state.current_focus}")
        print(f"  Iterations: {self.tui_state.iterations}")

        # Divider
        print()
        self.set_color("dim")
        print("─" * self.cols)
        self.set_color("reset")

        # Current prompt section
        print()
        self.set_color("bold")
        self.set_color("magenta")
        print("  CURRENT PROMPT:")
        self.set_color("reset")
        if self.tui_state.last_prompt:
            # Word wrap the prompt
            prompt_lines = []
            words = self.tui_state.last_prompt.split()
            line = "  "
            for word in words:
                if len(line) + len(word) + 1 > self.cols - 4:
                    prompt_lines.append(line)
                    line = "  " + word
                else:
                    line += (" " if line != "  " else "") + word
            prompt_lines.append(line)
            for pl in prompt_lines[:5]:  # Max 5 lines
                print(pl)
        else:
            print("  (waiting...)")

        # Result section
        print()
        self.set_color("bold")
        self.set_color("green")
        print("  LAST RESULT:")
        self.set_color("reset")
        if self.tui_state.last_result:
            print(f"  {self.tui_state.last_result[:self.cols-4]}")
        else:
            print("  (none yet)")

        # Insights section
        print()
        self.set_color("bold")
        self.set_color("yellow")
        print("  INSIGHTS:")
        self.set_color("reset")
        if self.tui_state.insights:
            for insight in self.tui_state.insights[-3:]:
                print(f"  • {insight[:self.cols-6]}")
        else:
            print("  (none yet)")

        # Divider
        print()
        self.set_color("dim")
        print("─" * self.cols)
        self.set_color("reset")

        # Log section (bottom area)
        log_start = 18
        log_height = self.rows - log_start - 4
        self.move_cursor(log_start, 1)
        self.set_color("bold")
        print("  ACTIVITY LOG:")
        self.set_color("reset")

        for msg in self.tui_state.log_messages[-(log_height):]:
            print(f"  {msg[:self.cols-4]}")

        # Commands footer
        self.move_cursor(self.rows - 2, 1)
        self.set_color("dim")
        print("─" * self.cols)
        self.set_color("cyan")
        print("  [SPACE] Pause/Resume  [R] Redirect  [I] Inject  [Q] Quit  [H] Help")
        self.set_color("reset")

        sys.stdout.flush()

    def input_thread(self):
        """Background thread to read keyboard input."""
        while self.running:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)
                if char:
                    self.input_queue.put(char)

    def self_prompt_loop(self):
        """Background thread for autonomous self-prompting."""
        while self.running:
            if self.tui_state.loop_state == LoopState.RUNNING:
                try:
                    # Generate next prompt
                    self.tui_state.add_log("Generating next prompt...")
                    next_prompt = self.prompter.generate_next_prompt()

                    self.tui_state.current_focus = next_prompt.get("focus", "Unknown")
                    self.tui_state.last_prompt = next_prompt.get("prompt", "")

                    self.tui_state.add_log(f"Focus: {self.tui_state.current_focus}")

                    # Simulate execution (in real version, would actually execute)
                    result = f"Executed: {next_prompt.get('prompt', '')[:50]}..."
                    insight = f"Learned: {next_prompt.get('expected', '')[:50]}"

                    self.tui_state.last_result = result

                    # Record result
                    self.prompter.record_result(
                        prompt=next_prompt.get("prompt", ""),
                        result=result,
                        insight=insight
                    )

                    self.tui_state.iterations = self.prompter.state.iterations
                    self.tui_state.insights = self.prompter.state.insights[-5:]
                    self.tui_state.add_log(f"Iteration {self.tui_state.iterations} complete")

                    # Wait before next iteration
                    for _ in range(50):  # 5 seconds, checking every 100ms
                        if not self.running or self.tui_state.loop_state != LoopState.RUNNING:
                            break
                        time.sleep(0.1)

                except Exception as e:
                    self.tui_state.add_log(f"Error: {e}")
                    time.sleep(1)
            else:
                time.sleep(0.1)

    def handle_input(self, char: str):
        """Handle user input."""
        char = char.lower()

        if char == ' ':  # Space = pause/resume
            if self.tui_state.loop_state == LoopState.RUNNING:
                self.tui_state.loop_state = LoopState.PAUSED
                self.tui_state.add_log("Paused by user")
            elif self.tui_state.loop_state == LoopState.PAUSED:
                self.tui_state.loop_state = LoopState.RUNNING
                self.tui_state.add_log("Resumed by user")
            else:  # STOPPED
                self.tui_state.loop_state = LoopState.RUNNING
                self.tui_state.add_log("Started by user")

        elif char == 'q':  # Quit
            self.running = False
            self.tui_state.loop_state = LoopState.STOPPED
            self.tui_state.add_log("Shutting down...")

        elif char == 'r':  # Redirect - change focus
            self.tui_state.add_log("Redirect mode - enter new focus:")
            # In a real implementation, would open input mode
            # For now, cycle through mock focuses
            focuses = [
                "Test Coverage",
                "Code Quality",
                "Documentation",
                "Performance",
                "Security",
            ]
            current_idx = focuses.index(self.tui_state.current_focus) if self.tui_state.current_focus in focuses else 0
            next_idx = (current_idx + 1) % len(focuses)
            self.tui_state.current_focus = focuses[next_idx]
            self.prompter.update_focus(focuses[next_idx])
            self.tui_state.add_log(f"Redirected to: {focuses[next_idx]}")

        elif char == 'i':  # Inject a custom prompt
            self.tui_state.add_log("Inject mode - would prompt for custom input")

        elif char == 'h':  # Help
            self.tui_state.add_log("Commands: SPACE=pause/resume, R=redirect, I=inject, Q=quit")

    def run(self):
        """Main TUI loop."""
        # Save terminal settings
        self.old_settings = termios.tcgetattr(sys.stdin)

        try:
            # Set terminal to raw mode for non-blocking input
            tty.setraw(sys.stdin.fileno())
            self.hide_cursor()

            # Start input thread
            input_thread = threading.Thread(target=self.input_thread, daemon=True)
            input_thread.start()

            # Start self-prompt thread
            prompt_thread = threading.Thread(target=self.self_prompt_loop, daemon=True)
            prompt_thread.start()

            # Initial state
            self.tui_state.iterations = self.prompter.state.iterations
            self.tui_state.current_focus = self.prompter.state.current_focus
            self.tui_state.loop_state = LoopState.PAUSED  # Start paused, let user start
            self.tui_state.add_log("Ouroboros TUI started")
            self.tui_state.add_log("Press SPACE to start autonomous loop")

            # Main display loop
            while self.running:
                self.draw_frame()

                # Process any input
                try:
                    while True:
                        char = self.input_queue.get_nowait()
                        self.handle_input(char)
                except Empty:
                    pass

                time.sleep(0.1)  # 10 FPS

        finally:
            # Restore terminal
            self.show_cursor()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            self.clear()
            print("Ouroboros TUI ended.")
            print(f"Total iterations: {self.tui_state.iterations}")
            print(f"State saved to: {self.state_dir}")


def run_tui(state_dir: Path):
    """Run the Ouroboros TUI."""
    tui = OuroborosTUI(state_dir)
    tui.run()


if __name__ == "__main__":
    import sys
    state_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".ouroboros")
    run_tui(state_dir)
