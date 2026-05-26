"""
LeetCode 评论爬虫 - 主程序
功能：爬取leetcode_problems.txt中每个问题的评论
"""

import time
import re
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


# 全局变量
result_lock = threading.Lock()
comments_dir = "leetcode_comments_output"
processed_count = 0
total_count = 0


def clean_text(text):
    if not text:
        return ""
    return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f​-‏ - ﻿]+', '', text)


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(3)
    driver.set_page_load_timeout(30)
    return driver


def is_member_problem(driver):
    """检查是否是会员题目"""
    try:
        # 会员题目会有锁定图标或提示
        lock_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'会员')]")
        if lock_elements:
            return True

        # 检查URL是否包含会员专属标记
        current_url = driver.current_url
        if "vip" in current_url.lower():
            return True

        return False
    except:
        return False


def crawl_single_problem(url, settings):
    """爬取单个问题的评论"""
    global processed_count

    sort_type = settings.get("sort_type", "最新")
    max_comments = settings.get("max_comments", 100)
    crawl_vip = settings.get("crawl_vip", False)

    driver = None
    comments = []

    for retry in range(2):
        try:
            driver = create_driver()
            driver.get(url)
            time.sleep(2)

            # 点击评论
            try:
                comment_div = driver.find_element(By.XPATH, "//div[contains(text(),'评论')]")
                comment_div.click()
                time.sleep(1.5)
            except:
                return url, [], False, "No_comment"

            # 检查是否需要登录（更精确的检测：评论区域内的登录提示）
            try:
                # 查找评论区域内是否有登录提示遮罩层
                login_mask = driver.find_elements(By.XPATH,
                    "//div[contains(@class,'opacity-0') or contains(@class,'pointer-events-none')]//*[contains(text(),'登录')]")
                if login_mask and not crawl_vip:
                    return url, [], False, "VIP_skip"
            except:
                pass

            # 排序
            try:
                sort_btn = driver.find_element(By.XPATH, "//button[contains(.,'排序:')]")
                sort_btn.click()
                time.sleep(0.3)

                if sort_type == "最新":
                    newest = driver.find_element(By.XPATH, "//div[contains(text(),'最新')]")
                    newest.click()
                else:
                    hot = driver.find_element(By.XPATH, "//div[contains(text(),'最热')]")
                    hot.click()
                time.sleep(1.5)
            except:
                pass  # 排序失败继续

            pages_needed = (max_comments + 9) // 10  # 每页约10条

            for page in range(1, pages_needed + 1):
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: len(d.find_elements(By.XPATH,
                            "//a[contains(@href, '/u/') and ancestor::div[contains(@class, 'flex items-center gap-1 truncate')]]")) > 0
                    )
                except:
                    pass

                page_comments = parse_page_comments(driver)
                if not page_comments:
                    break
                comments.extend(page_comments)

                if len(comments) >= max_comments:
                    comments = comments[:max_comments]
                    break

                if page < pages_needed:
                    try:
                        next_btn = driver.find_element(By.XPATH, f"//button[contains(text(),'{page + 1}')]")
                        next_btn.click()
                        time.sleep(0.5)
                    except:
                        break

            with result_lock:
                processed_count += 1
                if processed_count % 50 == 0:
                    print(f"  Progress: {processed_count}/{total_count}")

            return url, comments, True, "Success"

        except Exception as e:
            if retry < 1:
                time.sleep(1)
                continue
            with result_lock:
                processed_count += 1
            return url, [], False, str(e)[:30]

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass


def parse_page_comments(driver):
    comments = []

    user_links = driver.find_elements(By.XPATH,
        "//a[contains(@href, '/u/') and ancestor::div[contains(@class, 'flex items-center gap-1 truncate')]]")

    for link in user_links:
        try:
            href = link.get_attribute('href')
            if not href or '/u/' not in href:
                continue

            username = href.split('/u/')[1].rstrip('/')
            if not username:
                continue

            container = link
            for _ in range(15):
                try:
                    parent = container.find_element(By.XPATH, "..")
                    parent_class = parent.get_attribute('class') or ""
                    if 'gap-2' in parent_class and 'flex-col' in parent_class and 'flex w-full' in parent_class:
                        container = parent
                        break
                    container = parent
                except:
                    break

            try:
                ip_elem = container.find_element(By.XPATH, ".//span[contains(text(),'来自')]")
                ip_addr = clean_text(ip_elem.text.strip())
            except:
                ip_addr = "未知"

            try:
                time_elem = container.find_element(By.XPATH, ".//span[@data-state='closed']")
                comment_time = clean_text(time_elem.text.strip())
            except:
                comment_time = "未知"

            try:
                content_elem = container.find_element(By.XPATH, ".//div[contains(@class, 'markdown-content')]")
                content = clean_text(content_elem.text.strip())
            except:
                try:
                    p_elems = container.find_elements(By.XPATH, ".//p")
                    content = clean_text(" ".join([p.text.strip() for p in p_elems if p.text.strip()]))
                except:
                    content = "未知"

            comments.append({
                "user_id": username,
                "ip": ip_addr,
                "time": comment_time,
                "content": content
            })

        except Exception:
            continue

    return comments


def save_comments(comments, filepath):
    """保存评论到文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        for i, comment in enumerate(comments, 1):
            f.write(f"=== Comment {i} ===\n")
            f.write(f"User ID: {comment['user_id']}\n")
            f.write(f"IP/Location: {comment['ip']}\n")
            f.write(f"Time: {comment['time']}\n")
            f.write(f"Content: {comment['content']}\n\n")


def main():
    global total_count, processed_count

    print("=" * 60)
    print("LeetCode 评论爬虫")
    print("=" * 60)

    # ========== 用户设置 ==========
    # 1. 是否爬取会员题目
    print("\n[设置1] 是否爬取会员题目?")
    print("  会员题目需要登录才能查看完整评论")
    crawl_vip_input = input("  请输入 (y/n，默认n): ").strip().lower()
    crawl_vip = crawl_vip_input == 'y'

    if crawl_vip:
        print("\n  [提示] 请在打开的浏览器中登录LeetCode账号")
        print("  登录完成后在此窗口按回车继续...")
        input()

    # 2. 线程数
    print("\n[设置2] 请输入并行线程数 (默认5): ", end="")
    threads_input = input().strip()
    max_workers = int(threads_input) if threads_input.isdigit() else 5
    print(f"  使用 {max_workers} 个线程")

    # 3. 排序方式
    print("\n[设置3] 请选择排序方式:")
    print("  1. 最新")
    print("  2. 最热")
    sort_input = input("  请输入 (1/2，默认1): ").strip()
    sort_type = "最新" if sort_input != "2" else "最热"
    print(f"  选择: {sort_type}")

    # 4. 爬取评论数量
    print("\n[设置4] 请输入要爬取的评论数量 (默认100): ", end="")
    max_input = input().strip()
    max_comments = int(max_input) if max_input.isdigit() else 100
    print(f"  爬取前 {max_comments} 条评论")

    settings = {
        "crawl_vip": crawl_vip,
        "sort_type": sort_type,
        "max_comments": max_comments
    }

    # ========== 读取问题列表 ==========
    problems_file = "leetcode_problems.txt"
    if not os.path.exists(problems_file):
        print(f"\n错误: {problems_file} 不存在!")
        return

    with open(problems_file, "r", encoding="utf-8") as f:
        all_urls = [line.strip() for line in f if line.strip() and "leetcode.cn/problems/" in line]

    total_count = len(all_urls)
    print(f"\n共找到 {total_count} 个问题")

    # ========== 创建输出目录 ==========
    if not os.path.exists(comments_dir):
        os.makedirs(comments_dir)

    # 获取已爬取的问题
    existing_files = set()
    if os.path.exists(comments_dir):
        existing_files = set(f.name.replace('.txt', '') for f in os.scandir(comments_dir) if f.is_file() and f.name.endswith('.txt'))

    # 过滤未爬取的
    urls = []
    skipped_vip = 0
    for url in all_urls:
        slug = url.rstrip('/').split('/')[-1]
        if slug not in existing_files:
            urls.append(url)
        else:
            print(f"  已跳过 (已存在): {slug}")

    print(f"待爬取: {len(urls)} 个问题\n")

    if not urls:
        print("所有问题已爬取完成!")
        return

    # ========== 开始爬取 ==========
    print(f"开始爬取，使用 {max_workers} 线程，{sort_type}排序...\n")
    start_time = time.time()
    success_count = 0
    fail_count = 0
    skip_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(crawl_single_problem, url, settings): url for url in urls}

        for future in as_completed(futures):
            url = futures[future]
            try:
                problem_url, comments, success, msg = future.result()

                if msg == "VIP_skip":
                    print(f"[{processed_count}/{total_count}] {problem_url.split('/')[-1]} - 跳过(会员)")
                    skip_count += 1
                elif success and comments:
                    problem_slug = problem_url.rstrip('/').split('/')[-1]
                    output_file = os.path.join(comments_dir, f"{problem_slug}.txt")
                    save_comments(comments, output_file)
                    print(f"[{processed_count}/{total_count}] {problem_slug} - {len(comments)} comments")
                    success_count += 1
                else:
                    print(f"[{processed_count}/{total_count}] {problem_url.split('/')[-1]} - Failed ({msg})")
                    fail_count += 1

            except Exception as e:
                print(f"Error: {e}")

    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"爬取完成!")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"跳过(会员): {skip_count}")
    print(f"耗时: {total_time/60:.1f} 分钟")
    print(f"评论保存在: {comments_dir}/")


if __name__ == "__main__":
    main()