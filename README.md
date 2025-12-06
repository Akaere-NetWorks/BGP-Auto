# BGP Auto Configuration Generator

自动化BGP配置生成工具,根据TOML配置文件使用bgpq4生成过滤规则。

## 功能

- 读取config目录下的TOML配置文件
- 根据配置使用bgpq4查询AS信息
- 将查询结果保存到独立文件
- 合并所有结果到单一配置文件

## 目录结构

```
BGP-Auto/
├── config/           # 配置文件目录
│   └── stuix.toml   # 示例配置
├── output/          # 输出目录
│   └── stuix/       # 按配置文件名分组
│       ├── filters/ # 单独的过滤规则文件
│       └── filtersprefix.conf  # 合并后的文件
└── src/             # 源代码
    ├── main.py              # 主程序
    ├── config_parser.py     # 配置解析模块
    ├── bgp_query.py         # BGP查询模块
    └── file_merger.py       # 文件合并模块
```

## 配置文件格式

```toml
[DOWNSTREAM_PREFIX_AS215172]
enabled = true    # 是否启用
ipv6 = true      # 是否使用IPv6
from = "AS215172"  # AS号码

[DOWNSTREAM_PREFIX_AS211729]
enabled = true
ipv6 = true
from = "AS211729"
```

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

确保已安装bgpq4:
```bash
# Ubuntu/Debian
sudo apt install bgpq4

# macOS
brew install bgpq4
```

### 2. 运行程序

```bash
cd src
python main.py
```

程序会自动:
1. 扫描`config/`目录下所有`.toml`文件
2. 对每个启用的配置项执行bgpq4查询
3. 保存结果到`output/<配置文件名>/filters/`
4. 合并所有结果到`output/<配置文件名>/filtersprefix.conf`

## 输出示例

对于`config/stuix.toml`,输出结构如下:

```
output/stuix/
├── filters/
│   ├── DOWNSTREAM_PREFIX_AS215172.conf
│   └── DOWNSTREAM_PREFIX_AS211729.conf
└── filtersprefix.conf  # 合并后的文件
```

## 注意事项

- 确保bgpq4命令可用
- 配置文件必须是有效的TOML格式
- AS号码格式: "AS123456" 或 "123456"
- 只处理`enabled = true`的配置项

## 许可证

MIT
