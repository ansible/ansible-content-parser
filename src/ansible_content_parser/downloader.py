import os
import shutil
from git import Repo
from pathlib import Path


class Downloader():
    def __init__(self, work_dir, clear_work_dir=False):
        self.work_dir = work_dir
        if clear_work_dir and os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_repo_name(url):
        if url:
            if url.endswith('.git'):
                url = url[:-4]
            i = url.rfind('/')
            if i >= 0:
                url = url[i+1:]
        return url

    def extract(self, repo_url):
        repo_name = self.get_repo_name(repo_url)
        destination = Path(self.work_dir, repo_name)
        Repo.clone_from(repo_url, destination)

        return repo_name
