#!/usr/bin/env python3
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.generator import SiteGenerator
from backend.scheduler import DailyScheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='Deutsch News Generator')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler (daily at 18:00)')
    parser.add_argument('--time', default='18:00', help='Time for scheduled run (HH:MM)')
    args = parser.parse_args()

    if args.schedule:
        scheduler = DailyScheduler(args.time)
        scheduler.run_now()
        scheduler.start()
        try:
            while True:
                import time
                time.sleep(3600)
        except KeyboardInterrupt:
            scheduler.stop()
    else:
        generator = SiteGenerator()
        generator.generate()
        print("\n✅ Site generated successfully!")
        print(f"📁 Output: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))}")
        print("\nTo deploy to GitHub Pages:")
        print("1. Push the 'frontend' folder contents to your gh-pages branch")
        print("2. Or use: npx gh-pages -d frontend")

if __name__ == "__main__":
    main()