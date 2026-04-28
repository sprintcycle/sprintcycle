#!/usr/bin/env python3
"""
SprintCycle 30秒演示视频录制脚本
"""

import asyncio
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("/root/sprintcycle-projects/sprintcycle/videos")
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
VIDEO_OUTPUT = OUTPUT_DIR / "demo_30s.mp4"
TEMP_VIDEO = OUTPUT_DIR / "temp.mp4"

OUTPUT_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True, parents=True)

# 清理旧文件
for f in SCREENSHOT_DIR.glob("*.png"):
    f.unlink()
if TEMP_VIDEO.exists():
    TEMP_VIDEO.unlink()

async def capture_screenshots(page, duration, interval=0.1):
    """截取一系列截图，统一命名"""
    global frame_counter
    screenshots = []
    end_time = time.time() + duration
    
    while time.time() < end_time:
        await page.evaluate("document.body.style.backgroundColor = '#1a1a2e';")
        filename = SCREENSHOT_DIR / f"frame_{frame_counter:04d}.png"
        await page.screenshot(path=str(filename), type="png")
        screenshots.append(filename)
        frame_counter += 1
        await asyncio.sleep(interval)
    
    return screenshots

async def main():
    global frame_counter
    frame_counter = 0
    
    print("🚀 开始生成 SprintCycle 30秒演示视频...")
    all_count = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        print("📸 阶段1: 开场 Logo (0-5秒)...")
        intro_html = """<!DOCTYPE html><html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; font-family: -apple-system, sans-serif; }
        .logo { width: 120px; height: 120px; background: linear-gradient(135deg, #4ecdc4, #44a08d); border-radius: 28px; display: flex; align-items: center; justify-content: center; font-size: 48px; margin-bottom: 30px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.05); opacity: 0.9; } }
        h1 { font-size: 56px; font-weight: 700; color: #fff; margin-bottom: 10px; letter-spacing: -2px; }
        .subtitle { font-size: 20px; color: #4ecdc4; letter-spacing: 4px; text-transform: uppercase; }
        .tagline { margin-top: 30px; font-size: 16px; color: #888; }
        </style></head><body>
        <div class="logo">⚡</div>
        <h1>SprintCycle</h1>
        <div class="subtitle">AI-Driven Sprint Automation</div>
        <div class="tagline">自动化 • 智能化 • 高效迭代</div>
        </body></html>"""
        await page.goto(f"data:text/html,{intro_html}")
        await page.wait_for_timeout(300)
        await capture_screenshots(page, 4.5, interval=0.15)
        print(f"   完成: {frame_counter} 帧")
        
        print("📸 阶段2: 终端操作 (5-15秒, 2x快放)...")
        term_html = """<!DOCTYPE html><html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d1117; font-family: 'SF Mono', Monaco, monospace; padding: 40px; min-height: 100vh; }
        .terminal { background: #161b22; border-radius: 8px; padding: 20px; border: 1px solid #30363d; max-width: 900px; }
        .header { display: flex; gap: 8px; margin-bottom: 16px; }
        .btn { width: 12px; height: 12px; border-radius: 50%; }
        .btn.red { background: #ff5f56; } .btn.yellow { background: #ffbd2e; } .btn.green { background: #27ca40; }
        .prompt { color: #58a6ff; } .command { color: #c9d1d9; } .output { color: #8b949e; margin: 8px 0; }
        .success { color: #3fb950; }
        </style></head><body>
        <div class="terminal">
        <div class="header"><div class="btn red"></div><div class="btn yellow"></div><div class="btn green"></div></div>
        <div id="content"><div><span class="prompt">$</span> <span class="command">cd /root/sprintcycle-projects/sprintcycle</span></div><div class="output">/root/sprintcycle-projects/sprintcycle</div></div>
        </div>
        <script>
        const steps = [
            { delay: 200, html: '<div><span class="prompt">$</span> <span class="command">python cli.py status -p /root/technews</span></div>' },
            { delay: 400, html: '<div><span class="prompt">$</span> <span class="command">python cli.py status -p /root/technews</span></div><div class="output">Loading sprint cycle...</div>' },
            { delay: 700, html: '<div><span class="prompt">$</span> <span class="command">python cli.py status -p /root/technews</span></div><div class="output">Loading sprint cycle...<br>✓ Sprint: technews (2024-W17)</div>' },
            { delay: 1000, html: '<div><span class="prompt">$</span> <span class="command">python cli.py status -p /root/technews</span></div><div class="output">Loading sprint cycle...<br>✓ Sprint: technews (2024-W17)<br><span class="success">Status: Running | Tasks: 12 | Progress: 67%</span></div>' },
        ];
        let i = 0;
        function next() { if (i < steps.length) { document.getElementById("content").innerHTML += steps[i].html; i++; setTimeout(next, steps[i] ? steps[i].delay : 300); } }
        setTimeout(next, 100);
        </script></body></html>"""
        await page.goto(f"data:text/html,{term_html}")
        await page.wait_for_timeout(300)
        await capture_screenshots(page, 4.5, interval=0.12)
        print(f"   完成: {frame_counter} 帧")
        
        print("📸 阶段3: 前端展示 (15-25秒)...")
        frontend_html = """<!DOCTYPE html><html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); font-family: -apple-system, sans-serif; min-height: 100vh; padding: 20px; color: #fff; }
        .header { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; } .header .badge { background: #4ecdc4; color: #1a1a2e; padding: 6px 16px; border-radius: 20px; font-size: 14px; }
        .filters { display: flex; gap: 10px; margin-bottom: 20px; }
        .filter { background: rgba(255,255,255,0.1); padding: 10px 20px; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .filter.active { background: #4ecdc4; color: #1a1a2e; }
        .news-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .news-card { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: all 0.3s; }
        .news-card:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
        .news-card .tag { display: inline-block; background: #4ecdc4; color: #1a1a2e; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-bottom: 8px; }
        .news-card h3 { font-size: 16px; margin-bottom: 8px; line-height: 1.4; }
        .news-card .meta { font-size: 12px; color: #888; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat { background: rgba(255,255,255,0.05); padding: 16px 24px; border-radius: 12px; flex: 1; text-align: center; }
        .stat .value { font-size: 32px; font-weight: 700; color: #4ecdc4; }
        .stat .label { font-size: 14px; color: #888; }
        </style></head><body>
        <div class="header"><h1>⚡ TechNews</h1><span class="badge">LIVE</span></div>
        <div class="stats"><div class="stat"><div class="value">128</div><div class="label">Articles</div></div><div class="stat"><div class="value">45</div><div class="label">Categories</div></div><div class="stat"><div class="value">1.2k</div><div class="label">Readers</div></div></div>
        <div class="filters"><div class="filter active">All</div><div class="filter">AI</div><div class="filter">Tech</div><div class="filter">Startup</div><div class="filter">Dev</div></div>
        <div class="news-grid">
            <div class="news-card"><span class="tag">AI</span><h3>GPT-5 发布：OpenAI 开启 AI 新纪元</h3><div class="meta">10 分钟前 • 2.3k 阅读</div></div>
            <div class="news-card"><span class="tag">Tech</span><h3>苹果 Vision Pro 2 曝光：更轻薄</h3><div class="meta">25 分钟前 • 1.8k 阅读</div></div>
            <div class="news-card"><span class="tag">Startup</span><h3>估值 10 亿美元：AI 创业新星崛起</h3><div class="meta">1 小时前 • 956 阅读</div></div>
            <div class="news-card"><span class="tag">Dev</span><h3>TypeScript 6.0 正式发布</h3><div class="meta">2 小时前 • 3.1k 阅读</div></div>
            <div class="news-card"><span class="tag">AI</span><h3>Claude 4 发布：编程能力再突破</h3><div class="meta">3 小时前 • 4.2k 阅读</div></div>
            <div class="news-card"><span class="tag">Tech</span><h3>SpaceX 星舰第七次试飞成功</h3><div class="meta">4 小时前 • 5.6k 阅读</div></div>
        </div>
        <script>
        const filters = document.querySelectorAll('.filter');
        filters.forEach((f, i) => { setTimeout(() => { filters.forEach(x => x.classList.remove('active')); f.classList.add('active'); }, i * 1000); });
        const cards = document.querySelectorAll('.news-card');
        cards.forEach((c, i) => { setTimeout(() => { c.style.transform = 'translateY(-5px)'; c.style.background = 'rgba(78, 205, 196, 0.15)'; setTimeout(() => { c.style.transform = ''; c.style.background = ''; }, 500); }, 5000 + i * 500); });
        </script></body></html>"""
        await page.goto(f"data:text/html,{frontend_html}")
        await page.wait_for_timeout(300)
        await capture_screenshots(page, 9.5, interval=0.12)
        print(f"   完成: {frame_counter} 帧")
        
        print("📸 阶段4: 结尾 (25-30秒)...")
        outro_html = """<!DOCTYPE html><html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; font-family: -apple-system, sans-serif; }
        h2 { font-size: 36px; color: #fff; margin-bottom: 30px; }
        .github-link { display: flex; align-items: center; gap: 12px; background: #24292e; padding: 16px 32px; border-radius: 12px; color: #fff; font-size: 20px; text-decoration: none; margin-bottom: 30px; transition: all 0.3s; }
        .github-link:hover { background: #333; transform: scale(1.05); }
        .github-link svg { width: 28px; height: 28px; }
        .star-btn { display: flex; align-items: center; gap: 8px; background: #f05032; padding: 14px 28px; border-radius: 8px; color: #fff; font-size: 18px; border: none; cursor: pointer; transition: all 0.3s; }
        .star-btn:hover { background: #d43c24; transform: scale(1.05); }
        .thanks { margin-top: 40px; color: #888; font-size: 16px; }
        </style></head><body>
        <h2>Ready to Transform Your Sprint?</h2>
        <a href="https://github.com" class="github-link"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>github.com/sprintcycle/sprintcycle</a>
        <button class="star-btn">⭐ Star us on GitHub</button>
        <p class="thanks">感谢观看 / Thank You</p>
        </body></html>"""
        await page.goto(f"data:text/html,{outro_html}")
        await page.wait_for_timeout(300)
        await capture_screenshots(page, 4.5, interval=0.12)
        print(f"   完成: {frame_counter} 帧")
        
        await browser.close()
    
    total_frames = frame_counter
    print(f"\n📊 共生成 {total_frames} 帧截图")
    
    print("\n🎬 合成视频...")
    fps = total_frames / 30.0
    print(f"   帧率: {fps:.2f} fps")
    
    cmd = [
        'ffmpeg', '-y',
        '-framerate', f'{fps:.0f}',
        '-i', str(SCREENSHOT_DIR / 'frame_%04d.png'),
        '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        str(TEMP_VIDEO)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ ffmpeg 错误: {result.stderr[-500:]}")
        return False
    
    print(f"   视频生成成功")
    
    print("\n📦 压缩视频...")
    temp_size = TEMP_VIDEO.stat().st_size / (1024 * 1024)
    print(f"   原始大小: {temp_size:.2f} MB")
    
    crf = 23
    if temp_size > 5: crf = 28
    if temp_size > 10: crf = 32
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(TEMP_VIDEO),
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', str(crf),
        '-c:a', 'aac',
        '-b:a', '96k',
        '-movflags', '+faststart',
        str(VIDEO_OUTPUT)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  压缩警告: {result.stderr[-300:]}")
        import shutil
        shutil.copy(TEMP_VIDEO, VIDEO_OUTPUT)
    
    final_size = VIDEO_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"\n✅ 视频生成完成!")
    print(f"   输出: {VIDEO_OUTPUT}")
    print(f"   大小: {final_size:.2f} MB")
    print(f"   分辨率: 1280x720 (720p)")
    
    # 清理
    TEMP_VIDEO.unlink()
    for f in SCREENSHOT_DIR.glob("*.png"):
        f.unlink()

if __name__ == "__main__":
    asyncio.run(main())
