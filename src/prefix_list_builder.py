"""Static prefix list builder"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import re


class PrefixListBuilder:
    """Build static prefix list defines from local files"""

    def __init__(self, config_dir: Path, config_name: str, logger=None):
        self.config_dir = config_dir
        self.config_name = config_name
        self.logger = logger

    def build_all_conf(
        self, entries: List[Dict[str, Optional[str]]], output_dir: Path
    ) -> Optional[Path]:
        """
        Build all.conf with IPv4/IPv6 define blocks.

        Args:
            entries: List of dicts with optional ipv4/ipv6 list names
            output_dir: Output directory for all.conf

        Returns:
            Path to all.conf if created, otherwise None
        """
        blocks = []
        seen = set()

        for entry in entries:
            ipv6_name = entry.get("ipv6")
            ipv4_name = entry.get("ipv4")

            if ipv6_name and ipv6_name not in seen:
                seen.add(ipv6_name)
                ipv6_prefixes = self._load_prefixes(ipv6_name)
                if ipv6_prefixes:
                    blocks.append(self._render_define_block(ipv6_name, ipv6_prefixes))
                else:
                    self._log_warning(f"No IPv6 prefixes loaded for {ipv6_name}")

            if ipv4_name and ipv4_name not in seen:
                seen.add(ipv4_name)
                ipv4_prefixes = self._load_prefixes(ipv4_name)
                if ipv4_prefixes:
                    blocks.append(self._render_define_block(ipv4_name, ipv4_prefixes))
                else:
                    self._log_warning(f"No IPv4 prefixes loaded for {ipv4_name}")

        if not blocks:
            return None

        output_file = output_dir / "all.conf"
        with open(output_file, "w") as f:
            f.write("\n\n".join(blocks))
            if not blocks[-1].endswith("\n"):
                f.write("\n")

        if self.logger:
            self.logger.info(f"Saved to: {output_file}")
        else:
            print(f"Saved to: {output_file}")
        return output_file

    def build_all_conf_from_prefixes(
        self,
        ipv4_name: Optional[str],
        ipv6_name: Optional[str],
        ipv4_prefixes: Set[str],
        ipv6_prefixes: Set[str],
        output_dir: Path,
    ) -> Optional[Path]:
        """
        Build all.conf from in-memory prefix sets.

        Args:
            ipv4_name: Define name for IPv4 prefixes
            ipv6_name: Define name for IPv6 prefixes
            ipv4_prefixes: Set of IPv4 prefixes
            ipv6_prefixes: Set of IPv6 prefixes
            output_dir: Output directory for all.conf

        Returns:
            Path to all.conf if created, otherwise None
        """
        blocks = []

        if ipv6_name and ipv6_prefixes:
            blocks.append(self._render_define_block(ipv6_name, sorted(ipv6_prefixes)))

        if ipv4_name and ipv4_prefixes:
            blocks.append(self._render_define_block(ipv4_name, sorted(ipv4_prefixes)))

        if not blocks:
            return None

        output_file = output_dir / "all.conf"
        with open(output_file, "w") as f:
            f.write("\n\n".join(blocks))
            if not blocks[-1].endswith("\n"):
                f.write("\n")

        if self.logger:
            self.logger.info(f"Saved to: {output_file}")
        else:
            print(f"Saved to: {output_file}")
        return output_file

    def _load_prefixes(self, name: str) -> List[str]:
        prefix_file = self._find_prefix_file(name)
        if not prefix_file:
            self._log_warning(f"Prefix list file not found for {name}")
            return []

        try:
            content = prefix_file.read_text(encoding="utf-8")
        except Exception as e:
            self._log_warning(f"Failed to read prefix list {prefix_file}: {e}")
            return []

        prefixes: List[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith(";"):
                continue
            matches = re.findall(r"[0-9a-fA-F:\.]+/\d+", stripped)
            for match in matches:
                prefixes.append(match)

        return prefixes

    def _find_prefix_file(self, name: str) -> Optional[Path]:
        candidates: List[Path] = []
        name_path = Path(name)

        if name_path.is_absolute():
            candidates.append(name_path)
        else:
            if "/" in name or name.startswith("."):
                candidates.append(self.config_dir / name_path)

            config_subdir = self.config_dir / self.config_name
            candidates.append(config_subdir / name_path)
            candidates.append(self.config_dir / name_path)

            for ext in (".txt", ".conf", ".list"):
                candidates.append(config_subdir / f"{name}{ext}")
                candidates.append(self.config_dir / f"{name}{ext}")

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate

        return None

    def _render_define_block(self, name: str, prefixes: List[str]) -> str:
        lines = [f"define {name} = ["]
        for prefix in prefixes:
            lines.append(f"    {prefix},")
        lines.append("];\n")
        return "\n".join(lines)

    def parse_routes(self, content: str) -> Set[str]:
        routes: Set[str] = set()

        for line in content.split("\n"):
            line = line.strip()

            if not line or line.startswith("#") or line.startswith("define"):
                continue

            matches = re.findall(r"[0-9a-fA-F:\.]+/\d+", line)
            for match in matches:
                if "/" in match:
                    ip_part, prefix_part = match.rsplit("/", 1)
                    if ip_part and prefix_part.isdigit():
                        routes.add(match)

            if line.startswith("ip prefix"):
                parts = line.split()
                if len(parts) >= 3:
                    routes.add(parts[2])

        return routes

    def _log_warning(self, message: str):
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"Warning: {message}")
