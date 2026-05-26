# -*- coding: utf-8 -*-
"""
LeetCode 评论搜索工具
功能：搜索爬取的评论内容，查找包含关键词的问题和评论
"""

import os
import sys
import time

# 设置工作目录和编码
os.chdir(r'G:\project')
sys.stdout.reconfigure(encoding='utf-8')


def search_comments():
    print("=" * 60)
    print("LeetCode 评论搜索工具")
    print("=" * 60)

    comments_dir = "leetcode_comments_output"

    # ========== 用户输入关键词 ==========
    print("\n请输入要搜索的关键词（多个关键词用逗号分隔）:")
    print("例如: 字节,tiktok,抖音,bytedance,宇宙厂")

    try:
        keywords_input = input("> ").strip()
    except:
        keywords_input = ""

    if not keywords_input:
        print("未输入关键词，退出")
        return

    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
    if not keywords:
        print("关键词不能为空!")
        return

    print(f"\n搜索关键词: {keywords}")

    # ========== 检查目录 ==========
    if not os.path.exists(comments_dir):
        print(f"错误: {comments_dir} 目录不存在!")
        print("请先运行爬虫爬取评论")
        return

    # ========== 获取所有评论文件 ==========
    print("\n正在读取评论文件...")
    comment_files = [os.path.join(comments_dir, f) for f in os.listdir(comments_dir) if f.endswith('.txt')]
    print(f"共找到 {len(comment_files)} 个评论文件")

    # ========== 搜索 ==========
    print("\n开始搜索...")
    start_time = time.time()

    matched_results = {}

    for fp in comment_files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否包含关键词
            found_kws = [kw for kw in keywords if kw in content]
            if not found_kws:
                continue

            # 解析评论
            problem_url = f'https://leetcode.cn/problems/{os.path.basename(fp).replace(".txt", "")}/'
            comments_in_file = []
            current_comment = {}

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('=== Comment'):
                    if current_comment:
                        comments_in_file.append(current_comment)
                    current_comment = {}
                elif line.startswith('User ID:'):
                    current_comment['user_id'] = line.replace('User ID:', '').strip()
                elif line.startswith('IP/Location:'):
                    current_comment['ip'] = line.replace('IP/Location:', '').strip()
                elif line.startswith('Time:'):
                    current_comment['time'] = line.replace('Time:', '').strip()
                elif line.startswith('Content:'):
                    current_comment['content'] = line.replace('Content:', '').strip()

            if current_comment:
                comments_in_file.append(current_comment)

            # 找出命中关键词的评论（去重）
            seen_content = set()
            matched_comments = []
            for comment in comments_in_file:
                for kw in found_kws:
                    if kw in comment.get('content', ''):
                        content = comment.get('content', '')[:100]  # 用前100字符去重
                        if content not in seen_content:
                            seen_content.add(content)
                            matched_comments.append((kw, comment))
                        break

            if matched_comments:
                matched_results[problem_url] = {
                    'keywords': found_kws,
                    'matched_comments': matched_comments,
                    'total': len(comments_in_file)
                }

        except Exception as e:
            continue

    # ========== 排序 ==========
    sorted_results = sorted(matched_results.items(),
                            key=lambda x: len(x[1]['matched_comments']),
                            reverse=True)

    # ========== 保存结果 ==========
    output_file = "search_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('=' * 60 + '\n')
        f.write('LeetCode 评论搜索结果\n')
        f.write('=' * 60 + '\n\n')
        f.write(f'搜索关键词: {keywords}\n')
        f.write(f'搜索文件数: {len(comment_files)}\n')
        f.write(f'匹配问题数: {len(sorted_results)}\n')
        f.write(f'耗时: {time.time() - start_time:.1f} 秒\n\n')

        for i, (url, data) in enumerate(sorted_results, 1):
            f.write(f'{"="*60}\n')
            f.write(f'[{i}] {url}\n')
            f.write(f'    命中关键词: {", ".join(data["keywords"])}\n')
            f.write(f'    命中评论数: {len(data["matched_comments"])} / {data["total"]} 条\n')
            f.write(f'{"="*60}\n')
            f.write('命中评论内容:\n')
            f.write('-' * 60 + '\n')

            for idx, (kw, comment) in enumerate(data['matched_comments'], 1):
                f.write(f'\n  【评论 {idx}】\n')
                f.write(f'  用户ID: {comment.get("user_id", "N/A")}\n')
                f.write(f'  IP属地: {comment.get("ip", "N/A")}\n')
                f.write(f'  评论时间: {comment.get("time", "N/A")}\n')
                f.write(f'  命中关键词: {kw}\n')
                f.write(f'  评论内容:\n')
                f.write(f'{comment.get("content", "")}\n')
                f.write('-' * 60 + '\n')

            f.write('\n')

    # ========== 打印摘要 ==========
    print(f"\n{'='*60}")
    print(f"搜索完成!")
    print(f"共搜索 {len(comment_files)} 个文件")
    print(f"匹配 {len(sorted_results)} 个问题")
    print(f"结果保存到: {output_file}")

    print(f"\n前10个匹配 (按命中次数):")
    for i, (url, data) in enumerate(sorted_results[:10], 1):
        print(f"  {i}. {url}")
        print(f"     关键词: {', '.join(data['keywords'])} | 命中: {len(data['matched_comments'])} 条")


if __name__ == "__main__":
    search_comments()