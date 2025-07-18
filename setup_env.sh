#!/bin/bash

# Setup script for Flight Announcer environment variables
echo "Setting up Flight Announcer environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file and add your FlightAware API key"
else
    echo ".env file already exists"
fi

# Set environment variable for current session
if [ -z "$FLIGHTAWARE_API_KEY" ]; then
    echo ""
    echo "To set the API key for this session, run:"
    echo "export FLIGHTAWARE_API_KEY='v3P9XsAeKT9UXo5GQm8sq8HNGANXg5An'"
    echo ""
    echo "Or add it to your shell profile (.bashrc, .zshrc, etc.) to make it permanent"
else
    echo "FLIGHTAWARE_API_KEY is already set"
fi

echo "Setup complete!"