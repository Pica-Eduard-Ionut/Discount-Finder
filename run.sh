#!/bin/sh

echo "Running Lidl scraper..."
python lidl.py
sleep 5

echo "Running Penny scraper..."
python penny.py
sleep 5

echo "Starting web app..."
python app.py
