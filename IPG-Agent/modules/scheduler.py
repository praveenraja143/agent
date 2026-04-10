import schedule
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.tasks = []
        self.running = False

    def add_task(self, func, times):
        for t in times:
            schedule.every().day.at(t).do(func)
            self.tasks.append({'function': func.__name__, 'time': t})
            logger.info(f"Scheduled {func.__name__} at {t}")

    def run_pending(self):
        self.running = True
        logger.info("Scheduler started. Running pending tasks...")
        while self.running:
            schedule.run_pending()
            time.sleep(60)

    def tick(self):
        schedule.run_pending()

    def clear(self):
        schedule.clear()
        self.tasks.clear()

    def stop(self):
        self.running = False
        schedule.clear()
        logger.info("Scheduler stopped")

    def get_next_run(self):
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "No tasks scheduled"

    def get_all_tasks(self):
        jobs = schedule.get_jobs()
        return [str(j) for j in jobs]
