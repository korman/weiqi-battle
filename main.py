import subprocess
import threading
import queue
import time
import pathlib
import sys
from datetime import datetime
from openskill.models import PlackettLuce

PROJECT_ROOT = pathlib.Path(__file__).parent.absolute()
ENGINES_DIR = PROJECT_ROOT / "engines"
KATAGO_PATH = str(ENGINES_DIR / "katago.exe")
CONFIG_PATH = str(ENGINES_DIR / "default_gtp.cfg")
MODELS_DIR = ENGINES_DIR / "models"


class KataGoEngine:
    def __init__(self, model_path: str, name: str = "AI"):
        self.name = name
        self.model_path = model_path

        print(f"正在启动 {name}（模型：{model_path}）...")

        self.process = subprocess.Popen(
            [KATAGO_PATH, "gtp", "-model", model_path, "-config", CONFIG_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # 新增：捕获错误信息
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        self.response_queue = queue.Queue()
        threading.Thread(target=self._reader_thread, daemon=True).start()

        # 等待线程启动 + 引擎初始化
        time.sleep(0.5)

        # 如果 KataGo 进程已经异常退出，直接报错并打印原因
        if self.process.poll() is not None:
            stderr_output = self.process.stderr.read() or ""
            raise RuntimeError(
                f"{self.name} 启动失败（退出码 {self.process.returncode}）。"
                + (f"\nKataGo 错误信息：\n{stderr_output}" if stderr_output else "")
            )

        # 初始化 GTP
        self._send_init_commands()
        print(f"{name} 启动成功！")

    def _reader_thread(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            self.response_queue.put(line.strip())

    def _send_init_commands(self):
        self.send("boardsize 19")
        self.send("clear_board")
        self.send("komi 7.5")

    def send(self, cmd: str) -> str:
        print(f"   → 发送命令: {cmd}")

        # 如果进程已经退出，避免写入已关闭的管道
        if self.process.poll() is not None:
            stderr_output = self.process.stderr.read() or ""
            raise RuntimeError(
                f"{self.name} 已经退出，无法再发送命令：{cmd}。"
                + (f"\nKataGo 错误信息：\n{stderr_output}" if stderr_output else "")
            )

        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()

        response = []
        start_time = time.time()
        while True:
            try:
                line = self.response_queue.get(timeout=30)
                response.append(line)
                if line.startswith("=") or line.startswith("?"):
                    print(f"   ← 收到响应: {line}")
                    return "\n".join(response).strip()
            except queue.Empty:
                # 超时后打印 stderr 错误信息
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    print(f"KataGo 错误信息:\n{stderr_output}")
                raise RuntimeError(
                    f"{self.name} 响应超时！命令: {cmd}（已等待 {time.time() - start_time:.1f} 秒）"
                )

    def genmove(self, color: str) -> str:
        resp = self.send(f"genmove {color}")
        if resp.startswith("="):
            return resp[1:].strip().upper()
        raise RuntimeError(f"{self.name} genmove 出错")

    def play(self, color: str, move: str):
        self.send(f"play {color} {move}")

    def final_score(self) -> str:
        resp = self.send("final_score")
        if resp.startswith("="):
            score = resp[1:].strip().upper()
            return (
                "B"
                if score.startswith("B+")
                else "W"
                if score.startswith("W+")
                else "DRAW"
            )
        return "unknown"

    def close(self):
        self.send("quit")
        self.process.terminate()


# ====================== 配置 ======================
MODEL1 = str(MODELS_DIR / "kata1-zhizi-b28c512nbt-muonfd2.bin.gz")
MODEL2 = str(
    MODELS_DIR / "kata1-b28c512nbt-s8209287936-d4596492266.bin.gz"
)  # ← 改成你的第二个模型文件名


def play_match(
    engine_black: KataGoEngine, engine_white: KataGoEngine, max_moves: int = 400
):
    """让两个引擎对战一局，然后打印结果。"""
    moves = []
    consecutive_passes = 0

    current_color = "B"

    for move_no in range(1, max_moves + 1):
        if current_color == "B":
            move = engine_black.genmove("B")
            print(f"[{move_no}] 黑(模型1) 落子: {move}")

            # 同步局面到白方引擎
            engine_white.play("B", move)
        else:
            move = engine_white.genmove("W")
            print(f"[{move_no}] 白(模型2) 落子: {move}")

            # 同步局面到黑方引擎
            engine_black.play("W", move)

        moves.append((current_color, move))

        # 处理停着或认输
        upper_move = move.upper()
        if upper_move == "PASS":
            consecutive_passes += 1
        elif upper_move == "RESIGN":
            winner = "白" if current_color == "B" else "黑"
            print(f"对局结束：{winner} 方胜（{current_color} 方认输）")
            return
        else:
            consecutive_passes = 0

        if consecutive_passes >= 2:
            print("双方连续停着，进入结束结算。")
            break

        current_color = "W" if current_color == "B" else "B"

    # 让黑方引擎给出最后的胜负判断
    result = engine_black.final_score()
    if result == "B":
        print("最终结果：黑胜")
    elif result == "W":
        print("最终结果：白胜")
    elif result == "DRAW":
        print("最终结果：和局")
    else:
        print(f"最终结果未知：{result}")


# ====================== 运行 ======================
if __name__ == "__main__":
    # 检查 KataGo 可执行文件
    if not pathlib.Path(KATAGO_PATH).is_file():
        print(
            f"错误：未找到 KataGo 可执行文件：{KATAGO_PATH}\n"
            "请将 Windows 版 kataGo 可执行文件命名为 'katago.exe' 并放到 'engines' 目录下。"
        )
        sys.exit(1)

    # 检查模型文件是否存在
    missing_models = [m for m in (MODEL1, MODEL2) if not pathlib.Path(m).is_file()]
    if missing_models:
        print(
            "错误：以下模型文件不存在，请确认已经下载到 'engines/models' 目录下：\n"
            + "\n".join(f" - {m}" for m in missing_models)
        )
        sys.exit(1)

    engine1 = KataGoEngine(MODEL1, name="模型1（最强）")
    engine2 = KataGoEngine(MODEL2, name="模型2")
    print("两个引擎都已启动，开始对战。")

    try:
        play_match(engine1, engine2, max_moves=400)
    finally:
        # 确保引擎被正常关闭
        engine1.close()
        engine2.close()
