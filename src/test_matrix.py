#!/usr/bin/env python3

import time
import sys
import os

# Add the library path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../lib/rpi-rgb-led-matrix/bindings/python'))

from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for your setup
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'

matrix = RGBMatrix(options = options)

def draw_simple_text(matrix, text, x, y, r, g, b):
    """Draw simple text using pixel patterns (very basic)"""
    # Simple 3x5 font patterns for digits and 'x'
    patterns = {
        '0': [0b111, 0b101, 0b101, 0b101, 0b111],
        '1': [0b001, 0b001, 0b001, 0b001, 0b001],
        '2': [0b111, 0b001, 0b111, 0b100, 0b111],
        '3': [0b111, 0b001, 0b111, 0b001, 0b111],
        '4': [0b101, 0b101, 0b111, 0b001, 0b001],
        '5': [0b111, 0b100, 0b111, 0b001, 0b111],
        '6': [0b111, 0b100, 0b111, 0b101, 0b111],
        '7': [0b111, 0b001, 0b001, 0b001, 0b001],
        '8': [0b111, 0b101, 0b111, 0b101, 0b111],
        '9': [0b111, 0b101, 0b111, 0b001, 0b111],
        'x': [0b000, 0b101, 0b010, 0b101, 0b000]
    }
    
    char_x = x
    for char in text.lower():
        if char in patterns:
            pattern = patterns[char]
            for row in range(5):
                for col in range(3):
                    if pattern[row] & (1 << (2-col)):
                        matrix.SetPixel(char_x + col, y + row, r, g, b)
            char_x += 4  # Move to next character position

try:
    # Print dimensions first
    print(f"Matrix dimensions: {matrix.width}x{matrix.height}")
    print("Testing RGB Matrix - Press Ctrl+C to exit")
    sys.stdout.flush()
    
    # Clear the matrix
    matrix.Clear()
    
    # Test 1: Fill with red
    print("Filling with red...")
    sys.stdout.flush()
    for x in range(matrix.width):
        for y in range(matrix.height):
            matrix.SetPixel(x, y, 255, 0, 0)
    time.sleep(2)
    
    # Test 2: Fill with green
    print("Filling with green...")
    sys.stdout.flush()
    matrix.Clear()
    for x in range(matrix.width):
        for y in range(matrix.height):
            matrix.SetPixel(x, y, 0, 255, 0)
    time.sleep(2)
    
    # Test 3: Fill with blue
    print("Filling with blue...")
    sys.stdout.flush()
    matrix.Clear()
    for x in range(matrix.width):
        for y in range(matrix.height):
            matrix.SetPixel(x, y, 0, 0, 255)
    time.sleep(2)
    
    # Test 4: White border with dimensions text
    print("Drawing white border with dimensions...")
    sys.stdout.flush()
    matrix.Clear()
    
    # Draw white border
    for x in range(matrix.width):
        matrix.SetPixel(x, 0, 255, 255, 255)  # Top
        matrix.SetPixel(x, matrix.height-1, 255, 255, 255)  # Bottom
    for y in range(matrix.height):
        matrix.SetPixel(0, y, 255, 255, 255)  # Left
        matrix.SetPixel(matrix.width-1, y, 255, 255, 255)  # Right
    
    # Draw centered text showing dimensions
    text = f"{matrix.width}x{matrix.height}"
    text_width = len(text) * 4 - 1  # Each char is 4 pixels wide (3 + 1 space)
    x_pos = (matrix.width - text_width) // 2
    y_pos = (matrix.height - 5) // 2  # Center vertically (5 is font height)
    
    draw_simple_text(matrix, text, x_pos, y_pos, 0, 255, 0)  # Green text
    
    time.sleep(4)  # Show longer so you can read the text
    
    print("Test completed successfully!")
    print(f"Final check - Matrix dimensions: {matrix.width}x{matrix.height}")
    sys.stdout.flush()
    
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    matrix.Clear()