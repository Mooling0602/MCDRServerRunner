import subprocess
import sys
import threading
import queue
import select
import platform
from datetime import datetime

def read_output(pipe, callback):
    """使用 select 非阻塞读取管道内容并调用回调函数"""
    while True:
        ready, _, _ = select.select([pipe], [], [], 0.1)
        if ready:
            line = pipe.readline()
            if not line:
                break
            callback(line.rstrip())
        else:
            continue

def start_server(server_command):
    """启动Minecraft服务器进程"""
    return subprocess.Popen(
        server_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        text=True
    )

def input_thread(stop_event, input_queue):
    """在单独线程中非阻塞读取用户输入"""
    while not stop_event.is_set():
        try:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                line = sys.stdin.readline()
                if not line:
                    break
                input_queue.put(line.strip())
        except Exception:
            break

def shutdown_server(server_process):
    """发送 'stop' 命令关闭服务器，并等待其退出"""
    if server_process.poll() is None:
        try:
            server_process.stdin.write("stop\n")
            server_process.stdin.flush()
        except Exception:
            pass
        try:
            server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server_process.terminate()
            server_process.wait()

def main():
    # 如果不是 Windows 系统，则使用 stdbuf 强制 Java 输出行缓冲
    if platform.system() != "Windows":
        server_cmd = [
            'stdbuf', '-oL',
            'java',
            '-jar',
            'leaves-1.21.3.jar',
            'nogui'
        ]
    else:
        server_cmd = [
            'java',
            '-jar',
            'leaves-1.21.3.jar',
            'nogui'
        ]
    server_process = start_server(server_cmd)

    def handle_output(line):
        print(line, flush=True)

    stdout_thread = threading.Thread(
        target=read_output,
        args=(server_process.stdout, handle_output),
        daemon=True
    )
    stderr_thread = threading.Thread(
        target=read_output,
        args=(server_process.stderr, handle_output),
        daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    # 使用队列与非 daemon 的输入线程进行交互
    input_queue = queue.Queue()
    stop_event = threading.Event()
    inp_thread = threading.Thread(target=input_thread, args=(stop_event, input_queue))
    inp_thread.start()

    try:
        while True:
            # 如果服务器进程已退出，则退出主循环
            if server_process.poll() is not None:
                break

            try:
                user_input = input_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if user_input.lower() == 'exit':
                shutdown_server(server_process)
                break
            elif user_input.startswith('fakelog '):
                message = user_input[len('fakelog '):]
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp} INFO]: {message}", flush=True)
            else:
                if server_process.poll() is None:
                    server_process.stdin.write(user_input + "\n")
                    server_process.stdin.flush()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...", flush=True)
        shutdown_server(server_process)
    finally:
        # 通知输入线程退出，并等待其结束
        stop_event.set()
        inp_thread.join(timeout=1)
        if server_process.poll() is None:
            shutdown_server(server_process)
        # 可选：关闭 sys.stdin，确保退出时不再调用其方法
        try:
            sys.stdin.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()