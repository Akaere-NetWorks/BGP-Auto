"""BGP自动化配置生成器主程序"""
import sys
from pathlib import Path

from config_parser import ConfigParser
from bgp_query import BGPQuery
from file_merger import FileMerger
from logger import Logger
from html_generator import HTMLGenerator


def main():
    """主函数"""
    # 设置路径
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    output_dir = project_root / "output"
    log_dir = project_root / "logs"
    
    # Initialize logger
    logger = Logger(log_dir=log_dir)
    
    # Check config directory
    if not config_dir.exists():
        logger.error(f"Config directory does not exist {config_dir}")
        sys.exit(1)
    
    # Get all .toml config files
    config_files = list(config_dir.glob("*.toml"))
    
    if not config_files:
        logger.error(f"No .toml config files found in {config_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(config_files)} config file(s)")
    
    # Initialize HTML generator
    html_gen = HTMLGenerator(project_root)
    
    # 处理每个配置文件
    for config_file in config_files:
        process_config_file(config_file, output_dir, logger, html_gen)
    
    # Generate main index page
    logger.info("\nGenerating main index page...")
    index_file = html_gen.generate_index()
    logger.info(f"Main index saved to: {index_file}")


def process_config_file(config_file: Path, output_base_dir: Path, logger: Logger, html_gen: HTMLGenerator):
    """
    处理单个配置文件
    
    Args:
        config_file: 配置文件路径
        output_base_dir: 输出基础目录
        logger: Logger instance
        html_gen: HTMLGenerator instance
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Processing config file: {config_file.name}")
    logger.info(f"{'='*70}")
    
    # 根据配置文件名创建输出目录 (去掉.toml后缀)
    config_name = config_file.stem
    output_dir = output_base_dir / config_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse config
    parser = ConfigParser(config_file)
    try:
        parser.load_config()
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        return
    
    enabled_sections = parser.get_enabled_sections()
    
    if not enabled_sections:
        logger.warning(f"No enabled sections in config file {config_file.name}")
        return
    
    logger.info(f"Found {len(enabled_sections)} enabled section(s)")
    
    # 执行BGP查询
    bgp_query = BGPQuery(output_dir, logger)
    generated_files = []
    
    for section in enabled_sections:
        logger.info(f"\nProcessing: {section['name']}")
        logger.info(f"  AS Number: {section['from']}")
        logger.info(f"  IPv6: {section['ipv6']}")
        
        output_file = bgp_query.execute_query(
            section_name=section['name'],
            as_number=section['from'],
            ipv6=section['ipv6']
        )
        
        if output_file:
            generated_files.append(output_file)
    
    # Merge files
    merge_file = None
    if generated_files:
        logger.info(f"\nMerging {len(generated_files)} file(s)...")
        merger = FileMerger(output_dir, logger)
        merge_file = merger.merge_files(generated_files)
        logger.success(f"Config file {config_file.name} processed successfully")
    else:
        logger.warning(f"No files were generated")
    
    # Generate HTML report
    logger.info(f"\nGenerating HTML report...")
    html_file = html_gen.generate_report(
        config_name=config_name,
        sections=enabled_sections,
        generated_files=generated_files,
        merge_file=merge_file,
        logs=logger.get_logs()
    )
    logger.info(f"HTML detail page saved to: {html_file}")


if __name__ == "__main__":
    main()
