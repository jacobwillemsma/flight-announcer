#!/usr/bin/env python3
"""Test the new font characters for private jet display."""

# Test the font patterns
font_patterns = {
    '!': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100, 0b00000],
    "'": [0b00100, 0b00100, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
    '%': [0b10001, 0b10010, 0b00100, 0b00100, 0b01000, 0b01001, 0b10001, 0b00000],
}

def display_pattern(char, pattern):
    """Display a character pattern in ASCII art."""
    print(f"Character '{char}':")
    for row in pattern:
        line = ""
        for bit in range(5):  # 5 bits per row
            if row & (1 << (4-bit)):
                line += "█"  # Filled block
            else:
                line += " "  # Empty space
        print(f"  {line}")
    print()

def test_message():
    """Test the message 'Look! It's the 1%!'"""
    message = "Look! It's the 1%!"
    print(f"Testing message: '{message}'")
    print(f"Length: {len(message)} characters")
    print(f"Display width: {len(message) * 6} pixels")
    print(f"Fits in 128 pixels: {'Yes' if len(message) * 6 <= 128 else 'No'}")
    print()
    
    # Check for missing characters
    defined_chars = set(font_patterns.keys())
    message_chars = set(message)
    missing_chars = message_chars - defined_chars
    
    if missing_chars:
        print(f"Missing characters: {missing_chars}")
    else:
        print("All characters are defined!")
    print()
    
    # Display the new characters
    for char in ['!', "'", '%']:
        if char in font_patterns:
            display_pattern(char, font_patterns[char])

if __name__ == "__main__":
    test_message()