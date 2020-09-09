import re
import sys
import inspect
from random_pics.background import tasks


class BackgroundTaskManager:
    _instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(*args, **kwargs)
        return cls._instance

    def __init__(self):
        self.table = self.__init_table()
        self.current_task_name = None

    def __init_table(self):
        task_classes = {self.split_by_capitals(name): obj for name, obj in inspect.getmembers(sys.modules[tasks.__name__])
                        if self.is_task_class(obj)}
        return task_classes

    @staticmethod
    def split_by_capitals(name):
        lower_words = [word.lower() for word in re.findall(r'[A-Z][^A-Z]*', name)]
        return '_'.join(lower_words)

    @staticmethod
    def is_task_class(obj):
        return inspect.isclass(obj) and issubclass(obj, tasks.BaseTask) and obj is not tasks.BaseTask

    def add_background_task(self, task_name, app):
        self.current_task_name = task_name
        return self.start_background_task_async

    def start_background_task(self, task_name, app):
        self.current_task_name = task_name
        return self.start_background_task_async(app)

    async def start_background_task_async(self, app):
        task = self.table[self.current_task_name].as_task(app, self)
        app[self.current_task_name] = task


background_task_manager = BackgroundTaskManager()
