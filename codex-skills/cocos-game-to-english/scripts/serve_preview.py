#!/usr/bin/env python3
"""Serve an actual Cocos Web export on loopback; stops by itself after --idle-minutes without requests.

Never shared, never waited for (user 2026-10-23): every test line starts its own server on a new free port
(--port 0, the default) instead of waiting for another line's server. --snapshot first copies the export to a
private folder, so a build of the same game running at the same time cannot change the files under the test.
The server registers itself in browser_slots.py (old free ones are closed first) and frees its slot on exit.
Default URL is a centered fixed-size phone iframe (390x844); larger desktop windows never enlarge it.
--raw is internal automated QA only; it cannot be combined with --keep. Source/export bytes are never rewritten.
User trial (user 2026-10-23): the user plays in Codex's local preview. Start with --keep, put the printed link in the
Codex reply; never open the game in Ego for the user. No browser is opened by default (--open opens the system one).
"""
import argparse
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time
import webbrowser
from urllib.parse import parse_qs, urlsplit

LAST = [time.time()]


def phone_preview_html(width=390, height=844):
    """Keep the game iframe's CSS viewport fixed; only scale its outer presentation."""
    return ("""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="game-preview-mode" content="fixed-phone-v1"><title>手机试玩</title>
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#20242c}
body{display:grid;place-items:center}#phone-shell{position:relative;overflow:hidden;border-radius:12px;outline:1px solid #515762;box-shadow:0 12px 48px #0008;background:#fff}
#phone-game{position:absolute;left:0;top:0;border:0;display:block;transform-origin:top left;background:#fff}</style>
</head><body><main id="phone-shell" aria-label="手机尺寸游戏试玩"><iframe id="phone-game" title="游戏试玩" allow="autoplay; gamepad"></iframe></main>
<script>(()=>{const width=__WIDTH__,height=__HEIGHT__,shell=document.getElementById('phone-shell'),frame=document.getElementById('phone-game');
frame.style.width=width+'px';frame.style.height=height+'px';
const game=new URL('index.html',location.href);game.search=location.search;game.searchParams.set('__phone_game','1');frame.src=game.pathname+game.search+location.hash;
function fit(){const scale=Math.min(1,Math.max(1,innerWidth-32)/width,Math.max(1,innerHeight-32)/height);shell.style.width=width*scale+'px';shell.style.height=height*scale+'px';frame.style.transform='scale('+scale+')';window.__phonePreview={policy:'fixed-phone-v1',width,height,scale};}
addEventListener('resize',fit);fit();})();</script></body></html>""".replace('__WIDTH__',str(width)).replace('__HEIGHT__',str(height))).encode('utf-8')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, phone_size=None, **kwargs):
        self.phone_size = phone_size
        super().__init__(*args, **kwargs)

    def do_GET(self):
        LAST[0] = time.time()
        request = urlsplit(self.path)
        if (self.phone_size and request.path in ('/', '/index.html')
                and parse_qs(request.query).get('__phone_game') != ['1']):
            content = phone_preview_html(*self.phone_size)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        super().do_GET()

    def log_message(self, *args):   # quiet: no line per request
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true', help='default now (kept for old commands)')
    parser.add_argument('--open', action='store_true', help='also open the system browser (never Ego for the user; see --keep)')
    parser.add_argument('--idle-minutes', type=float, default=20, help='stop after this many minutes without requests (0 = never)')
    parser.add_argument('--snapshot', action='store_true', help='serve a private copy of the export (a running build cannot change it)')
    parser.add_argument('--name', default='', help='label shown in browser_slots.py list, e.g. "测试线 音量复核"')
    parser.add_argument('--project', help='game folder (label only)')
    parser.add_argument('--keep', action='store_true', help='user trial link the agent gives in Codex (local preview): never closed as idle by a sweep')
    parser.add_argument('--orientation', choices=['portrait', 'landscape'], default='portrait', help='user preview phone orientation (default portrait 390x844)')
    parser.add_argument('--phone-width', type=int, help='fixed inner CSS viewport width; use with --phone-height')
    parser.add_argument('--phone-height', type=int, help='fixed inner CSS viewport height; use with --phone-width')
    parser.add_argument('--raw', action='store_true', help='internal automated QA only: expose top-level original canvas; never hand this URL to a user')
    args = parser.parse_args()
    if (args.phone_width is None) != (args.phone_height is None):
        parser.error('--phone-width and --phone-height must be supplied together')
    phone_size = (args.phone_width, args.phone_height) if args.phone_width is not None else ((844, 390) if args.orientation == 'landscape' else (390, 844))
    if any(value < 200 or value > 1600 for value in phone_size):
        parser.error('phone viewport dimensions must be between 200 and 1600 CSS pixels')
    if args.raw and args.keep:
        parser.error('--raw is internal QA only and cannot be combined with user-trial --keep')
    directory = args.directory.resolve()
    if not (directory / 'index.html').is_file():
        raise SystemExit('找不到 index.html，请指定实际 Cocos Web 导出目录。')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import browser_slots
        browser_slots.sweep(close=True)                     # close free old test windows / servers first
    except Exception:
        browser_slots = None
    if args.snapshot:
        if browser_slots is None:
            raise SystemExit('--snapshot needs browser_slots.py next to this script')
        directory = browser_slots.snapshot(directory)
    handler = partial(Handler, directory=str(directory), phone_size=None if args.raw else phone_size)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    url = f'http://127.0.0.1:{server.server_port}/'
    slot = None
    if browser_slots is not None:
        try:
            slot = browser_slots.register('preview', args.name or directory.name, os.getpid(), args.project,
                                          port=server.server_port, url=url, directory=directory if args.snapshot else None,
                                          keep=args.keep or args.idle_minutes == 0)
        except Exception:
            slot = None
    lifetime = '用户试玩保留中；不因空闲时间自动关闭。' if args.keep or args.idle_minutes == 0 else f'{args.idle_minutes:g} 分钟没人访问会自动关闭。'
    entry_kind = '内部QA入口（禁止交给用户试玩）' if args.raw else f'手机尺寸本地试玩（内部 {phone_size[0]}×{phone_size[1]}，只缩小不放大）'
    print(f'{entry_kind}：{url}\n（给用户试玩：把这个链接写在 Codex 回复里，用户在 Codex 里打开本地预览；不要在 Ego 里打开交给用户。）\n保持窗口打开；按 Control+C 结束。{lifetime}'
          + (f'\n（独立副本：{directory}）' if args.snapshot else ''), flush=True)
    if slot:
        def beat():
            seen = 0
            while True:
                time.sleep(15)
                if LAST[0] != seen:
                    seen = LAST[0]
                    try:
                        browser_slots.heartbeat(slot, heartbeat_ts=LAST[0])
                    except Exception:
                        pass
        threading.Thread(target=beat, daemon=True).start()
    if args.idle_minutes > 0 and not args.keep:
        def watch():
            while True:
                time.sleep(15)
                if time.time() - LAST[0] > args.idle_minutes * 60:
                    print('长时间没人访问，预览服务已自动关闭。', flush=True)
                    server.shutdown()
                    return
        threading.Thread(target=watch, daemon=True).start()
    import signal
    def stop(signum, frame):
        raise KeyboardInterrupt                         # SIGTERM from a sweep: still free our slot below
    for sig in (getattr(signal, 'SIGTERM', None), getattr(signal, 'SIGBREAK', None)):
        if sig is not None:
            try:
                signal.signal(sig, stop)
            except (OSError, ValueError):
                pass
    if args.open and not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if slot:
            browser_slots.release(slot)                   # also deletes the private snapshot copy


if __name__ == '__main__':
    main()
