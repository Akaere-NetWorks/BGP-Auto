"""BGP查询执行模块"""
import subprocess
from pathlib import Path
from typing import Optional


class BGPQuery:
    """执行bgpq4命令并保存结果"""
    
    def __init__(self, output_dir: Path, logger=None):
        self.output_dir = output_dir
        self.filters_dir = output_dir / "filters"
        self.filters_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def execute_query(self, section_name: str, as_number: str, ipv6: bool = False) -> Optional[Path]:
        """
        执行bgpq4查询
        
        Args:
            section_name: 配置段名称
            as_number: AS号码
            ipv6: 是否使用IPv6
            
        Returns:
            保存的文件路径,如果失败则返回None
        """
        output_file = self.filters_dir / f"{section_name}.conf"
        
        # 构建命令
        cmd = ["bgpq4"]
        if ipv6:
            cmd.append("-6")
        cmd.extend(["-b", "-l", f"define {section_name}", as_number])
        
        try:
            if self.logger:
                self.logger.info(f"Executing command: {' '.join(cmd)}")
            else:
                print(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Save output to file
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            
            if self.logger:
                self.logger.info(f"Saved to: {output_file}")
            else:
                print(f"Saved to: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"Execution failed: {e}")
                self.logger.error(f"Error output: {e.stderr}")
            else:
                print(f"Execution failed: {e}")
                print(f"Error output: {e.stderr}")
            return None
        except FileNotFoundError:
            if self.logger:
                self.logger.error("bgpq4 command not found, please ensure it is installed")
            else:
                print("Error: bgpq4 command not found, please ensure it is installed")
            return None
