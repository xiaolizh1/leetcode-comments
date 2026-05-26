# LeetCode 评论爬虫与搜索工具

LeetCode 中国站评论爬虫，支持多线程并行爬取和关键词搜索过滤。

## 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `leetcode_crawler_v2.py` | **评论爬虫主程序** - 爬取LeetCode问题的用户评论 |
| `leetcode_search.py` | **搜索工具（交互式）** - 在已爬取的评论中搜索关键词 |
| `leetcode_comments_output/` | **评论输出目录** - 存放爬取的评论文件 |

### 依赖

```bash
pip install selenium
```

还需要安装 Chrome WebDriver（确保版本与Chrome浏览器一致）。

## 使用方法

### 1. 爬取评论 (leetcode_crawler_v2.py)

运行前需先准备问题列表文件 `leetcode_problems.txt`，每行一个问题URL：
```
https://leetcode.cn/problems/two-sum/
https://leetcode.cn/problems/add-two-numbers/
...
```

运行爬虫：
```bash
python leetcode_crawler_v2.py
```

程序会依次询问：
1. **是否爬取会员题目** - 输入 `y` 需要登录，不输入则跳过会员题
2. **并行线程数** - 默认5，建议5-10
3. **排序方式** - 1=最新，2=最热
4. **评论数量** - 默认100条

**输出**：评论会保存到 `leetcode_comments_output/{题目slug}.txt`

**已爬取的问题会自动跳过**，再次运行不会重复爬取。

#### 快速测试（5个问题，最热排序，不登陆）
```bash
python test_crawler.py
```

### 2. 搜索评论 (leetcode_search.py)

在已爬取的评论文件中按关键词搜索。

```bash
python leetcode_search.py
```

程序会提示输入关键词（多个用逗号分隔）：
```
请输入要搜索的关键词（多个关键词用逗号分隔）:
例如: 字节,tiktok,抖音,bytedance,宇宙厂
>
```

**搜索结果**会保存到 `search_results.txt`，包含：
- 匹配的问题链接
- 命中的关键词
- 每条匹配的评论内容（用户ID、IP属地、时间、命中关键词、评论内容）

### 3. 离线搜索脚本 (run_search.py)

已内置关键词的搜索脚本，适合快速重复搜索：
```bash
python run_search.py
```

默认搜索关键词：`['字节', 'tiktok', '抖音', 'bytedance', '宇宙厂']`

## 评论文件格式

爬取到的评论文件格式如下（`leetcode_comments_output/{slug}.txt`）：

```
=== Comment 1 ===
User ID: user_name
IP/Location: 来自 北京
Time: 2026.03.14
Content: 评论内容文字

=== Comment 2 ===
User ID: another_user
IP/Location: 来自 上海
Time: 2026.03.15
Content: 另一条评论内容
```

## 批量爬取

如果需要一次性爬取大量问题，建议：

1. 先获取问题列表（可从LeetCode页面爬取所有问题URL）
2. 将URL保存到 `leetcode_problems.txt`
3. 运行爬虫，设置适当的线程数（建议5-10）

```bash
# 示例：批量爬取前1000个问题
python leetcode_crawler_v2.py
# 输入：n（不爬会员题）
# 输入：10（10线程）
# 输入：2（最热排序）
# 输入：100（每题100条评论）
```

## 常见问题

**Q: 爬虫被检测怎么办？**
A: 降低线程数，延长sleep时间，或使用代理IP。

**Q: 会员题目无法爬取？**
A: 需要登录LeetCode账号，在爬取时选择爬取会员题目选项，并按提示完成登录。

**Q: 搜索结果重复？**
A: 这是因为同一用户发了多条相同评论。搜索结果会根据内容去重。

## License

MIT