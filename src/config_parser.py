"""配置文件解析模块"""

import tomli
from pathlib import Path
from typing import Dict, List


class ConfigParser:
    """解析TOML配置文件"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_data = {}

    def load_config(self) -> Dict:
        """加载配置文件"""
        with open(self.config_path, "rb") as f:
            self.config_data = tomli.load(f)
        return self.config_data

    def get_enabled_sections(self) -> List[Dict]:
        """获取所有启用的配置项"""
        enabled_sections = []

        for section_name, section_data in self.config_data.items():
            if not section_data.get("enabled", False):
                continue

            if "from" in section_data:
                enabled_sections.append(
                    {
                        "name": section_name,
                        "type": "bgp",
                        "ipv6": section_data.get("ipv6", False),
                        "from": section_data.get("from", ""),
                    }
                )
            else:
                enabled_sections.append(
                    {
                        "name": section_name,
                        "type": "static",
                        "ipv6": section_data.get("ipv6"),
                        "ipv4": section_data.get("ipv4"),
                    }
                )

        return enabled_sections
