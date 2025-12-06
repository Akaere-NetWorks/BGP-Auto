"""BGP自动化配置生成器主程序"""
import sys
from pathlib import Path

from config_parser import ConfigParser
from bgp_query import BGPQuery
from file_merger import FileMerger


def main():
    """主函数"""
    # 设置路径
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    output_dir = project_root / "output"
    
    # Check config directory
    if not config_dir.exists():
        print(f"Error: Config directory does not exist {config_dir}")
        sys.exit(1)
    
    # Get all .toml config files
    config_files = list(config_dir.glob("*.toml"))
    
    if not config_files:
        print(f"Error: No .toml config files found in {config_dir}")
        sys.exit(1)
    
    print(f"Found {len(config_files)} config file(s)")
    
    # 处理每个配置文件
    for config_file in config_files:
        process_config_file(config_file, output_dir)


def process_config_file(config_file: Path, output_base_dir: Path):
    """
    处理单个配置文件
    
    Args:
        config_file: 配置文件路径
        output_base_dir: 输出基础目录
    """
    print(f"\n{'='*70}")
    print(f"Processing config file: {config_file.name}")
    print(f"{'='*70}")
    
    # 根据配置文件名创建输出目录 (去掉.toml后缀)
    config_name = config_file.stem
    output_dir = output_base_dir / config_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse config
    parser = ConfigParser(config_file)
    try:
        parser.load_config()
    except Exception as e:
        print(f"Error: Failed to load config file: {e}")
        return
    
    enabled_sections = parser.get_enabled_sections()
    
    if not enabled_sections:
        print(f"Warning: No enabled sections in config file {config_file.name}")
        return
    
    print(f"Found {len(enabled_sections)} enabled section(s)")
    
    # 执行BGP查询
    bgp_query = BGPQuery(output_dir)
    generated_files = []
    
    for section in enabled_sections:
        print(f"\nProcessing: {section['name']}")
        print(f"  AS Number: {section['from']}")
        print(f"  IPv6: {section['ipv6']}")
        
        output_file = bgp_query.execute_query(
            section_name=section['name'],
            as_number=section['from'],
            ipv6=section['ipv6']
        )
        
        if output_file:
            generated_files.append(output_file)
    
    # Merge files
    if generated_files:
        print(f"\nMerging {len(generated_files)} file(s)...")
        merger = FileMerger(output_dir)
        merger.merge_files(generated_files)
        print(f"\n✓ Config file {config_file.name} processed successfully")
    else:
        print(f"\nWarning: No files were generated")


if __name__ == "__main__":
    main()
