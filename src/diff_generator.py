"""Diff generator module for comparing route changes across git history"""
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class DiffGenerator:
    """Generate diffs for route configuration changes across git history"""

    def __init__(self, project_root: Path, history_count: int = 5, logger=None):
        """
        Initialize diff generator

        Args:
            project_root: Project root directory
            history_count: Number of historical commits to compare (default: 5)
            logger: Optional logger instance
        """
        self.project_root = project_root
        self.history_count = history_count
        self.logger = logger
        self.output_dir = project_root / "output"

    def get_git_history(self, file_path: Path, count: int = None) -> List[Dict]:
        """
        Get git history for a specific file

        Args:
            file_path: Path to the file
            count: Number of commits to retrieve (default: self.history_count)

        Returns:
            List of dicts with commit info (hash, date, author, message)
        """
        if count is None:
            count = self.history_count

        try:
            cmd = [
                "git", "log",
                f"-{count}",
                "--pretty=format:%H|%ai|%an|%s",
                "--", str(file_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            'hash': parts[0],
                            'date': parts[1],
                            'author': parts[2],
                            'message': parts[3]
                        })

            return commits

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.warning(f"Failed to get git history for {file_path}: {e}")
            return []
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting git history: {e}")
            return []

    def get_file_at_commit(self, file_path: Path, commit_hash: str) -> Optional[str]:
        """
        Get file content at a specific commit

        Args:
            file_path: Path to the file
            commit_hash: Git commit hash

        Returns:
            File content as string, or None if not found
        """
        try:
            cmd = ["git", "show", f"{commit_hash}:{file_path}"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                return result.stdout
            return None

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to get file at {commit_hash}: {e}")
            return None

    def parse_routes(self, content: str) -> set:
        """
        Parse route prefixes from bgpq4 output

        Args:
            content: BGP configuration file content

        Returns:
            Set of route prefixes
        """
        routes = set()
        for line in content.split('\n'):
            line = line.strip()
            # Match route prefixes (IPv4 and IPv6)
            # Typical format: "ip prefix 1.2.3.0/24" or "ip prefix 2001:db8::/32"
            if line.startswith('ip prefix'):
                parts = line.split()
                if len(parts) >= 3:
                    routes.add(parts[2])
            # Also match exact format
            elif line and not line.startswith('#') and not line.startswith('define'):
                # Try to extract CIDR notation
                import re
                cidr_match = re.search(r'([0-9a-fA-F:\.]+)/\d+', line)
                if cidr_match:
                    routes.add(cidr_match.group(1) + '/' + line.split('/')[1].split()[0] if '/' in line else cidr_match.group(0))
        return routes

    def compare_routes(self, old_routes: set, new_routes: set) -> Dict:
        """
        Compare two sets of routes

        Args:
            old_routes: Set of old routes
            new_routes: Set of new routes

        Returns:
            Dict with added, removed, and unchanged routes
        """
        return {
            'added': sorted(new_routes - old_routes),
            'removed': sorted(old_routes - new_routes),
            'unchanged': sorted(old_routes & new_routes),
            'old_count': len(old_routes),
            'new_count': len(new_routes)
        }

    def generate_diff_for_file(self, config_name: str, section_name: str) -> List[Dict]:
        """
        Generate diff history for a specific filter file

        Args:
            config_name: Configuration name
            section_name: Section name (e.g., DOWNSTREAM_PREFIX_AS215172)

        Returns:
            List of diff comparisons
        """
        file_path = self.output_dir / config_name / "filters" / f"{section_name}.conf"

        if not file_path.exists():
            if self.logger:
                self.logger.warning(f"File not found: {file_path}")
            return []

        # Get current content
        try:
            with open(file_path, 'r') as f:
                current_content = f.read()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to read current file: {e}")
            return []

        current_routes = self.parse_routes(current_content)

        # Get git history
        history = self.get_git_history(file_path)

        diffs = []
        for commit in history:
            old_content = self.get_file_at_commit(file_path, commit['hash'])
            if old_content:
                old_routes = self.parse_routes(old_content)
                comparison = self.compare_routes(old_routes, current_routes)

                diffs.append({
                    'commit': commit,
                    'comparison': comparison
                })

        return diffs

    def generate_all_diffs(self, config_name: str, sections: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Generate diffs for all sections in a config

        Args:
            config_name: Configuration name
            sections: List of section dicts

        Returns:
            Dict mapping section names to their diff histories
        """
        all_diffs = {}

        for section in sections:
            section_name = section['name']
            diffs = self.generate_diff_for_file(config_name, section_name)
            if diffs:
                all_diffs[section_name] = diffs

        return all_diffs

    def generate_merged_diff(self, config_name: str) -> List[Dict]:
        """
        Generate diff history for the merged configuration file

        Args:
            config_name: Configuration name

        Returns:
            List of diff comparisons for merged file
        """
        file_path = self.output_dir / config_name / "filtersprefix.conf"

        if not file_path.exists():
            return []

        # Get current content
        try:
            with open(file_path, 'r') as f:
                current_content = f.read()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to read merged file: {e}")
            return []

        current_routes = self.parse_routes(current_content)

        # Get git history
        history = self.get_git_history(file_path)

        diffs = []
        for commit in history:
            old_content = self.get_file_at_commit(file_path, commit['hash'])
            if old_content:
                old_routes = self.parse_routes(old_content)
                comparison = self.compare_routes(old_routes, current_routes)

                diffs.append({
                    'commit': commit,
                    'comparison': comparison
                })

        return diffs
