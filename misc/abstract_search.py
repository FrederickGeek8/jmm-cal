#!/usr/bin/env python3
"""
Interactive Text Search Application using curses
Displays a search box and filters items as the user types.
"""

import curses
import json
import urllib.request
import textwrap
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
CACHE_DIR = CURRENT_DIR / "abstract_cache/"
assert CACHE_DIR.is_dir()

def show_popup(stdscr, title, message):
    """
    Display a centered popup dialog with a title, message, and optional items list.
    Returns when user presses any key.
    """
    max_y, max_x = stdscr.getmaxyx()
    items = []

    wrapped_msg = textwrap.wrap(message, width=max_x - 12)
    if wrapped_msg is not None:
        items += wrapped_msg
    else:
        items += [message]

    items += [""]


    popup_width = max(len(line) for line in [title] + items) + 6
    popup_height = len(items) + 6

    # Ensure popup fits on screen
    popup_width = min(popup_width, max_x - 4)
    popup_height = min(popup_height, max_y - 4)

    # Calculate center position
    start_y = (max_y - popup_height) // 2
    start_x = (max_x - popup_width) // 2

    # Create a new window for the popup
    popup_win = curses.newwin(popup_height, popup_width, start_y, start_x)
    popup_win.box()

    # Draw title
    title_x = (popup_width - len(title)) // 2
    popup_win.addstr(1, title_x, title, curses.A_BOLD)
    popup_win.addstr(2, 1, "─" * (popup_width - 2))

    # Draw message and items
    current_line = 3
    # popup_win.addstr(current_line, 3, message[:popup_width - 6])
    # current_line += 1

    if items:
        current_line += 1
        for item in items:
            if current_line < popup_height - 2:
                display_item = item[:popup_width - 6] if len(item) > popup_width - 6 else item
                popup_win.addstr(current_line, 3, display_item)
                current_line += 1

    # Draw footer
    footer = "Press any key to continue"
    footer_x = (popup_width - len(footer)) // 2
    popup_win.addstr(popup_height - 2, footer_x, footer, curses.A_DIM)

    popup_win.refresh()
    popup_win.getch()

def lookup_abstract(id: str) -> str:
    # check if in cache
    cache_file = CACHE_DIR / f"{id}_abstract.txt"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return f.read()

    try:
        url = f"https://meetings.ams.org/math/jmm2026/meetingapi.cgi/Paper/{id}"
        with urllib.request.urlopen(url) as req:
            data = json.loads(req.read().decode())

        if "RawAbstract" in data:
            with open(cache_file, 'w') as f:
                f.write(data["RawAbstract"])

            return data["RawAbstract"]
        else:
            return "Abstract not found."

    except Exception as e:
        print(e)
        raise e

def main(stdscr):
    # Sample data - a list of items to search through
    with open(CURRENT_DIR / "../site/resources/jmm2026-parsed-agenda.json", 'r') as f:
        object = json.load(f)
        # print(list(object[0].keys()))
        filtered = list(filter(lambda o: "presno" in o, object))
        jmm_kv = dict(zip(map(lambda o: o["title"], filtered), filtered))

    items = list(jmm_kv.keys())

    # Initialize curses settings
    curses.curs_set(1)  # Show cursor
    stdscr.clear()

    # Variables to track state
    search_text = ""
    selected_index = 0
    max_y, max_x = stdscr.getmaxyx()

    while True:
        stdscr.clear()

        # Filter items based on search text (case-insensitive, starts with)
        if search_text:
            filtered_items = [
                item for item in items
                if search_text.lower() in item.lower()
            ]
        else:
            filtered_items = items

        # Ensure selected index is within bounds
        if filtered_items:
            selected_index = min(selected_index, len(filtered_items) - 1)
            selected_index = max(selected_index, 0)
        else:
            selected_index = 0

        # Display title
        title = "JMM Abstract Search"
        stdscr.addstr(0, 0, title, curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * len(title))

        # Display search box
        stdscr.addstr(3, 0, "Search: ")
        stdscr.addstr(3, 8, search_text)
        stdscr.addstr(4, 0, "-" * (max_x - 1))

        # Display filtered items
        stdscr.addstr(5, 0, f"Results ({len(filtered_items)} items):", curses.A_BOLD)

        # Calculate how many items we can display
        available_lines = max_y - 7  # Reserve space for header and footer
        display_items = filtered_items[:available_lines]

        for idx, item in enumerate(display_items):
            try:
                # Highlight the selected item
                if idx == selected_index:
                    stdscr.addstr(6 + idx, 2, f"> {item}", curses.A_REVERSE)
                else:
                    stdscr.addstr(6 + idx, 2, f"  {item}")
            except curses.error:
                # Skip if we run out of screen space
                break

        # Display help text at bottom
        help_text = "Type to search | ↑/↓ to select | Enter to choose | Backspace to delete | ESC to exit"
        try:
            stdscr.addstr(max_y - 1, 0, help_text, curses.A_DIM)
        except curses.error:
            pass

        # Position cursor at the end of search text
        stdscr.move(3, 8 + len(search_text))

        # Refresh screen
        stdscr.refresh()

        # Get user input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break

        # Handle different key inputs
        if key == 27:  # ESC key
            break
        elif key == curses.KEY_UP:  # Up arrow
            if selected_index > 0:
                selected_index -= 1
        elif key == curses.KEY_DOWN:  # Down arrow
            if filtered_items and selected_index < len(filtered_items) - 1:
                selected_index += 1
        elif key in (curses.KEY_ENTER, 10, 13):  # Enter key
            if filtered_items:
                # User selected an item - show popup
                selected_item = filtered_items[selected_index]
                abstract = lookup_abstract(jmm_kv[selected_item]['presno'])
                show_popup(stdscr,
                           f"Abstract for: \"{selected_item}\"",
                           f"Abstract:\n{abstract}",
                )
                # Continue running after popup closes
        elif key in (curses.KEY_BACKSPACE, 127, 8):  # Backspace
            search_text = search_text[:-1]
            selected_index = 0  # Reset selection when search changes
        elif key == curses.KEY_RESIZE:
            # Handle terminal resize
            max_y, max_x = stdscr.getmaxyx()
        elif 32 <= key <= 126:  # Printable ASCII characters
            search_text += chr(key)
            selected_index = 0  # Reset selection when search changes


if __name__ == "__main__":
    try:
        curses.wrapper(main)
        print("\nApplication closed.")
    except KeyboardInterrupt:
        print("\nApplication closed.")
