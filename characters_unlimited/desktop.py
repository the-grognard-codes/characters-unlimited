"""Desktop controller for the bundled local browser application."""
import argparse
import os
from pathlib import Path
import threading
import traceback
import webbrowser

from .application import CharacterApplication
from .server import create_server


def main():
    parser = argparse.ArgumentParser(description='Characters Unlimited')
    parser.add_argument('--data-dir', type=Path, default=Path(os.getenv('LOCALAPPDATA', Path.home())) / 'CharactersUnlimited')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--headless', action='store_true', help='Run without the desktop controller for packaged validation')
    parser.add_argument('--no-browser', action='store_true', help='Open the workshop using the controller button')
    arguments = parser.parse_args()
    server = None
    try:
        server = create_server(CharacterApplication(arguments.data_dir), arguments.port)
        if arguments.headless:
            try:
                server.serve_forever()
            finally:
                server.server_close()
            return
        import tkinter as tk
        from tkinter import ttk
        window = tk.Tk()
        window.title('Characters Unlimited')
        window.resizable(False, False)
        frame = ttk.Frame(window, padding=20)
        frame.pack()
        url = f'http://127.0.0.1:{server.server_address[1]}/'
        ttk.Label(frame, text='Characters Unlimited', font=('Segoe UI', 16)).pack(anchor='w')
        ttk.Label(frame, text='Your character workshop is running on this PC.').pack(anchor='w', pady=(8, 0))
        ttk.Label(frame, text='Wait for Saved on this PC in the workshop before stopping.').pack(anchor='w', pady=(4, 12))
        ttk.Button(frame, text='Open character workshop', command=lambda: webbrowser.open(url)).pack(fill='x')
        def stop():
            server.shutdown()
            server.server_close()
            window.destroy()
        ttk.Button(frame, text='Stop application', command=stop).pack(fill='x', pady=(8, 0))
        window.protocol('WM_DELETE_WINDOW', stop)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        if not arguments.no_browser:
            webbrowser.open(url)
        window.mainloop()
    except Exception:
        details = traceback.format_exc()
        log = arguments.data_dir / 'startup-error.log'
        try:
            arguments.data_dir.mkdir(parents=True, exist_ok=True)
            log.write_text(details, encoding='utf-8')
            diagnostic = f'Details were saved to:\n{log}'
        except OSError:
            diagnostic = 'The character-data directory could not be written. Check its location and permissions.'
        if arguments.headless:
            raise SystemExit(1)
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, f'The workshop could not start. {diagnostic}',
                                       'Characters Unlimited', 0x10)
        raise SystemExit(1)
    finally:
        if server is not None:
            server.server_close()


if __name__ == '__main__':
    main()
