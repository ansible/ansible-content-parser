"""Download git repositories."""
from pathlib import Path

from git import Repo


class Downloader:
    """The Downloader class."""

    def __init__(self, work_dir: str) -> None:
        """Initialize the Downloader class."""
        self.work_dir = work_dir
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_repo_name(url: str) -> str:
        """Extract the repository name from a given URL string."""
        if url:
            if url.endswith(".git"):
                url = url[:-4]
            i = url.rfind("/")
            if i >= 0:
                url = url[i + 1 :]
        return url

    def extract(self, repo_url: str) -> str:
        """Extract a given git repository by cloning."""
        repo_name = self.get_repo_name(repo_url)
        destination = Path(self.work_dir, repo_name)
        Repo.clone_from(repo_url, destination)

        return repo_name
