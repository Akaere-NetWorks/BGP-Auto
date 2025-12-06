"""文件合并模块"""
from pathlib import Path
from typing import List


class FileMerger:
    """合并多个配置文件"""
    
    def __init__(self, output_dir: Path, logger=None):
        self.output_dir = output_dir
        self.filters_dir = output_dir / "filters"
        self.logger = logger
    
    def merge_files(self, file_list: List[Path], output_filename: str = "filtersprefix.conf") -> Path:
        """
        合并多个文件到一个文件
        
        Args:
            file_list: 要合并的文件路径列表
            output_filename: 输出文件名
            
        Returns:
            合并后的文件路径
        """
        output_file = self.output_dir / output_filename
        
        with open(output_file, 'w') as out_f:
            for i, file_path in enumerate(file_list):
                if not file_path.exists():
                    if self.logger:
                        self.logger.warning(f"File does not exist {file_path}")
                    else:
                        print(f"Warning: File does not exist {file_path}")
                    continue
                
                # Add separator comments
                if i > 0:
                    out_f.write("\n# " + "="*70 + "\n")
                
                out_f.write(f"# Source: {file_path.name}\n")
                out_f.write("# " + "="*70 + "\n\n")
                
                # Read and write file content
                with open(file_path, 'r') as in_f:
                    content = in_f.read()
                    out_f.write(content)
                    
                    # Ensure each file ends with newline
                    if not content.endswith('\n'):
                        out_f.write('\n')
        
        if self.logger:
            self.logger.info(f"Merged to: {output_file}")
        else:
            print(f"Merged to: {output_file}")
        return output_file
