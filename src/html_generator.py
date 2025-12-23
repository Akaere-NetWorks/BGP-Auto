"""HTML report generator module"""
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class HTMLGenerator:
    """Generate HTML status report"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.html_dir = project_root / "html"
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.reports = []  # Store all config reports for index

    def generate_report(self, config_name: str, sections: List[Dict],
                       generated_files: List[Path], merge_file: Path = None, logs: List = None) -> Path:
        """
        Generate HTML status report

        Args:
            config_name: Configuration file name
            sections: List of processed sections
            generated_files: List of generated files
            merge_file: Merged file path
            logs: Log messages

        Returns:
            Path to generated HTML file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Store report info for index
        self.reports.append({
            'config_name': config_name,
            'timestamp': timestamp,
            'total': len(sections),
            'success': len(generated_files),
            'failed': len(sections) - len(generated_files)
        })

        # Generate detail page
        detail_file = self.html_dir / f"{config_name}_detail.html"
        detail_content = self._generate_detail_page(config_name, sections, generated_files, merge_file, logs, timestamp)
        with open(detail_file, 'w', encoding='utf-8') as f:
            f.write(detail_content)

        # Generate content pages for each generated file
        for file_path in generated_files:
            self._generate_content_page(config_name, file_path)

        # Generate merged file content page
        if merge_file and merge_file.exists():
            self._generate_merged_content_page(config_name, merge_file)

        return detail_file

    def generate_diff_pages(self, config_name: str, sections: List[Dict],
                           all_diffs: Dict[str, List[Dict]], merged_diffs: List[Dict] = None):
        """
        Generate HTML pages for route change diffs

        Args:
            config_name: Configuration name
            sections: List of sections
            all_diffs: Dict mapping section names to diff histories
            merged_diffs: Diff history for merged file
        """
        # Generate main diff index page
        self._generate_diff_index(config_name, sections, all_diffs, merged_diffs)

        # Generate individual diff pages for each section
        for section_name, diffs in all_diffs.items():
            if diffs:
                self._generate_section_diff_page(config_name, section_name, diffs)

        # Generate diff page for merged file
        if merged_diffs:
            self._generate_merged_diff_page(config_name, merged_diffs)

    def _generate_diff_index(self, config_name: str, sections: List[Dict],
                            all_diffs: Dict[str, List[Dict]], merged_diffs: List[Dict]):
        """Generate diff index page"""
        diff_index_file = self.html_dir / f"{config_name}_diff_index.html"

        # Build section links
        section_links = ""
        for section in sections:
            section_name = section['name']
            if section_name in all_diffs and all_diffs[section_name]:
                latest_diff = all_diffs[section_name][0]['comparison']
                section_links += f"""
                <tr>
                    <td><a href="{config_name}_{section_name}_diff.html">{section_name}</a></td>
                    <td>{section['from']}</td>
                    <td>{latest_diff['old_count']} → {latest_diff['new_count']}</td>
                    <td style='color: green;'>+{len(latest_diff['added'])}</td>
                    <td style='color: red;'>-{len(latest_diff['removed'])}</td>
                </tr>
                """
            else:
                section_links += f"""
                <tr>
                    <td>{section_name}</td>
                    <td>{section['from']}</td>
                    <td colspan='3'>No history available</td>
                </tr>
                """

        # Build merged diff link
        merged_info = ""
        if merged_diffs:
            latest_diff = merged_diffs[0]['comparison']
            merged_info = f"""
            <tr>
                <td colspan='5'><hr></td>
            </tr>
            <tr>
                <td><a href="{config_name}_merged_diff.html"><strong>Merged Configuration (filtersprefix.conf)</strong></a></td>
                <td>All Sections</td>
                <td>{latest_diff['old_count']} → {latest_diff['new_count']}</td>
                <td style='color: green;'>+{len(latest_diff['added'])}</td>
                <td style='color: red;'>-{len(latest_diff['removed'])}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Route Changes - {config_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .added {{ color: green; }}
        .removed {{ color: red; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <p><a href="{config_name}_detail.html">&lt; Back to Detail</a> | <a href="index.html">Home</a></p>
    <h1>Route Change History</h1>
    <p>Configuration: {config_name}</p>
    <p>Showing changes compared to previous commits</p>

    <hr>

    <h2>Summary</h2>
    <table>
        <tr>
            <th>Section</th>
            <th>AS Number</th>
            <th>Route Count</th>
            <th>Added</th>
            <th>Removed</th>
        </tr>
        {section_links}
        {merged_info}
    </table>

    <hr>
    <p><small>Changes are shown between current version and most recent historical commit</small></p>
</body>
</html>"""

        with open(diff_index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_section_diff_page(self, config_name: str, section_name: str, diffs: List[Dict]):
        """Generate diff page for a specific section"""
        diff_file = self.html_dir / f"{config_name}_{section_name}_diff.html"

        # Build diff history
        diff_history = ""
        for i, diff_item in enumerate(diffs):
            commit = diff_item['commit']
            comp = diff_item['comparison']

            added_list = "<br>".join(comp['added']) if comp['added'] else "<em>None</em>"
            removed_list = "<br>".join(comp['removed']) if comp['removed'] else "<em>None</em>"

            diff_history += f"""
            <div style="border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; background-color: #fafafa;">
                <h3>Compare to: {commit['message']}</h3>
                <p><strong>Commit:</strong> {commit['hash'][:8]}</p>
                <p><strong>Date:</strong> {commit['date']}</p>
                <p><strong>Author:</strong> {commit['author']}</p>

                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%; vertical-align: top;">
                            <h4 style="color: green;">Added Routes (+{len(comp['added'])})</h4>
                            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px;">
                                {added_list}
                            </div>
                        </td>
                        <td style="width: 50%; vertical-align: top;">
                            <h4 style="color: red;">Removed Routes (-{len(comp['removed'])})</h4>
                            <div style="background-color: #ffebee; padding: 10px; border-radius: 5px;">
                                {removed_list}
                            </div>
                        </td>
                    </tr>
                </table>

                <p><strong>Summary:</strong> Routes changed from {comp['old_count']} to {comp['new_count']}
                   (Δ {comp['new_count'] - comp['old_count']:+d})</p>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Route Changes - {section_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .added {{ color: green; }}
        .removed {{ color: red; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <p><a href="{config_name}_diff_index.html">&lt; Back to Diff Index</a> |
       <a href="{config_name}_detail.html">Detail</a> |
       <a href="index.html">Home</a></p>
    <h1>Route Change History: {section_name}</h1>

    <hr>

    {diff_history}

    <hr>
</body>
</html>"""

        with open(diff_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_merged_diff_page(self, config_name: str, diffs: List[Dict]):
        """Generate diff page for merged configuration"""
        diff_file = self.html_dir / f"{config_name}_merged_diff.html"

        # Build diff history
        diff_history = ""
        for i, diff_item in enumerate(diffs):
            commit = diff_item['commit']
            comp = diff_item['comparison']

            added_list = "<br>".join(comp['added']) if comp['added'] else "<em>None</em>"
            removed_list = "<br>".join(comp['removed']) if comp['removed'] else "<em>None</em>"

            diff_history += f"""
            <div style="border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; background-color: #fafafa;">
                <h3>Compare to: {commit['message']}</h3>
                <p><strong>Commit:</strong> {commit['hash'][:8]}</p>
                <p><strong>Date:</strong> {commit['date']}</p>
                <p><strong>Author:</strong> {commit['author']}</p>

                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%; vertical-align: top;">
                            <h4 style="color: green;">Added Routes (+{len(comp['added'])})</h4>
                            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                                {added_list}
                            </div>
                        </td>
                        <td style="width: 50%; vertical-align: top;">
                            <h4 style="color: red;">Removed Routes (-{len(comp['removed'])})</h4>
                            <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                                {removed_list}
                            </div>
                        </td>
                    </tr>
                </table>

                <p><strong>Summary:</strong> Routes changed from {comp['old_count']} to {comp['new_count']}
                   (Δ {comp['new_count'] - comp['old_count']:+d})</p>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Merged Route Changes - {config_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .added {{ color: green; }}
        .removed {{ color: red; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <p><a href="{config_name}_diff_index.html">&lt; Back to Diff Index</a> |
       <a href="{config_name}_detail.html">Detail</a> |
       <a href="index.html">Home</a></p>
    <h1>Merged Configuration Route Changes</h1>
    <p>Configuration: {config_name}</p>
    <p>File: filtersprefix.conf</p>

    <hr>

    {diff_history}

    <hr>
</body>
</html>"""

        with open(diff_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def generate_index(self):
        """Generate main index page"""
        index_file = self.html_dir / "index.html"

        reports_rows = ""
        for report in self.reports:
            reports_rows += f"""
            <tr>
                <td><a href="{report['config_name']}_detail.html">{report['config_name']}</a></td>
                <td>{report['timestamp']}</td>
                <td>{report['total']}</td>
                <td>{report['success']}</td>
                <td>{report['failed']}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BGP Auto - Main Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; background-color: white; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f0f0f0; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .success {{ color: green; font-weight: bold; }}
        .failed {{ color: red; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #777; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>BGP Auto Configuration Generator</h1>
        <p>Automated BGP route filtering configuration system</p>

        <h2>Configuration Reports</h2>
        <table>
            <tr>
                <th>Config Name</th>
                <th>Generated Time</th>
                <th>Total Sections</th>
                <th>Success</th>
                <th>Failed</th>
            </tr>
            {reports_rows}
        </table>

        <div class="footer">
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return index_file
    
    def _generate_detail_page(self, config_name: str, sections: List[Dict],
                      generated_files: List[Path], merge_file: Path = None, logs: List = None, timestamp: str = None) -> str:
        """Generate detail page HTML content"""

        total_sections = len(sections)
        success_count = len(generated_files)
        failed_count = total_sections - success_count

        # Build sections table
        sections_rows = ""
        for i, section in enumerate(sections):
            status = "<span class='success'>✓</span>" if i < success_count else "<span class='failed'>✗</span>"

            sections_rows += f"""
            <tr>
                <td>{i + 1}</td>
                <td>{section['name']}</td>
                <td>{section['from']}</td>
                <td>{'Yes' if section['ipv6'] else 'No'}</td>
                <td>{status}</td>
            </tr>
            """

        # Build files list with links
        files_list = ""
        for file_path in generated_files:
            file_size = file_path.stat().st_size if file_path.exists() else 0
            content_file = f"{config_name}_{file_path.stem}_content.html"
            files_list += f"<li><a href=\"{content_file}\">{file_path.name}</a> <span style='color: #888;'>({file_size} bytes)</span></li>\n"

        merge_info = ""
        if merge_file and merge_file.exists():
            merge_size = merge_file.stat().st_size
            merged_content_file = f"{config_name}_merged_content.html"
            merge_info = f"<p><strong>Merged File:</strong> <a href=\"{merged_content_file}\">{merge_file.name}</a> <span style='color: #888;'>({merge_size} bytes)</span></p>"

        # Build logs
        logs_content = ""
        if logs:
            for level, message in logs:
                logs_content += f"<div>[{level}] {message}</div>\n"

        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BGP Auto Report - {config_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; background-color: white; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f0f0f0; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .success {{ color: green; font-weight: bold; }}
        .failed {{ color: red; font-weight: bold; }}
        .nav {{ padding: 10px; background-color: #e8f5e9; border-radius: 5px; margin-bottom: 20px; }}
        .nav a {{ margin-right: 15px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-item {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
        .summary-item h3 {{ margin: 0; color: #4CAF50; }}
        .summary-item p {{ margin: 5px 0 0; font-size: 1.5em; font-weight: bold; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ padding: 8px; border-bottom: 1px solid #eee; }}
        li:last-child {{ border-bottom: none; }}
        .diff-link {{ display: inline-block; margin-top: 10px; padding: 10px 20px; background-color: #2196F3; color: white; border-radius: 5px; }}
        .diff-link:hover {{ background-color: #0b7dda; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="index.html">&larr; Back to Index</a>
        </div>

        <h1>BGP Auto Configuration Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Configuration:</strong> {config_name}</p>

        <h2>Summary</h2>
        <div class="summary">
            <div class="summary-item">
                <h3>Total Sections</h3>
                <p>{total_sections}</p>
            </div>
            <div class="summary-item">
                <h3 style="color: #4CAF50;">Success</h3>
                <p style="color: #4CAF50;">{success_count}</p>
            </div>
            <div class="summary-item">
                <h3 style="color: #f44336;">Failed</h3>
                <p style="color: #f44336;">{failed_count}</p>
            </div>
        </div>
        <a href="{config_name}_diff_index.html" class="diff-link">View Route Change History</a>

        <h2>Processing Details</h2>
        <table>
            <tr>
                <th>#</th>
                <th>Section Name</th>
                <th>AS Number</th>
                <th>IPv6</th>
                <th>Status</th>
            </tr>
            {sections_rows}
        </table>

        <h2>Generated Files</h2>
        <ul>
            {files_list}
        </ul>

        {merge_info}

        <h2>Logs</h2>
        <pre>
{logs_content}
        </pre>
    </div>
</body>
</html>"""

        return html_template
    
    def _generate_content_page(self, config_name: str, file_path: Path):
        """Generate content page for a specific file"""
        content_file = self.html_dir / f"{config_name}_{file_path.stem}_content.html"

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file: {e}"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{file_path.name} - Content</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .nav {{ padding: 10px; background-color: #e8f5e9; border-radius: 5px; margin-bottom: 20px; }}
        .nav a {{ margin-right: 15px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.9em; line-height: 1.5; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="{config_name}_detail.html">&larr; Back to Detail</a>
            <a href="index.html">Home</a>
        </div>
        <h1>File Content: {file_path.name}</h1>
        <pre>{content}</pre>
    </div>
</body>
</html>"""

        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_merged_content_page(self, config_name: str, merge_file: Path):
        """Generate content page for merged file"""
        content_file = self.html_dir / f"{config_name}_merged_content.html"

        # Read file content
        try:
            with open(merge_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file: {e}"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{merge_file.name} - Merged Content</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .nav {{ padding: 10px; background-color: #e8f5e9; border-radius: 5px; margin-bottom: 20px; }}
        .nav a {{ margin-right: 15px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.9em; line-height: 1.5; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="{config_name}_detail.html">&larr; Back to Detail</a>
            <a href="index.html">Home</a>
        </div>
        <h1>Merged File Content: {merge_file.name}</h1>
        <pre>{content}</pre>
    </div>
</body>
</html>"""

        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
