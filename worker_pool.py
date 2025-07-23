import concurrent.futures
from typing import List, Callable
from config import Config

class WorkerPool:
    def __init__(self, max_workers: int = Config.MAX_WORKERS):
        self.max_workers = max_workers
    
    def process_batch(self, items: List, process_func: Callable) -> List:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process_func, item, worker_id) 
                      for worker_id, item in enumerate(items)]
            return [future.result() for future in concurrent.futures.as_completed(futures)]