import schedule
import time
import logging
import threading
from datetime import datetime
from backend.generator import SiteGenerator

logger = logging.getLogger(__name__)

class DailyScheduler:
    def __init__(self, run_time="18:00"):
        self.run_time = run_time
        self.generator = SiteGenerator()
        self.running = False
        self.thread = None
    
    def run_once(self):
        logger.info(f"Running scheduled generation at {datetime.now().strftime('%H:%M')}")
        try:
            self.generator.generate()
            logger.info("Generation completed successfully")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
    
    def start(self):
        schedule.every().day.at(self.run_time).do(self.run_once)
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Scheduler started - will run daily at {self.run_time}")
    
    def stop(self):
        self.running = False
        schedule.clear()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run_loop(self):
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def run_now(self):
        self.run_once()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler = DailyScheduler("18:00")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        scheduler.run_now()
    else:
        scheduler.run_now()
        scheduler.start()
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            scheduler.stop()