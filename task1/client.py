import argparse
import os
import socket

BUFFER_SIZE = 64 * 1024
ENCODING = "utf-8"


class ServerDisconnected(Exception):
    pass


def recv_line(sock: socket.socket) -> str:
    data = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            if not data:
                raise ServerDisconnected("Server disconnected")
            break
        if chunk == b"\n":
            break
        data.extend(chunk)
    return data.decode(ENCODING, errors="replace").rstrip("\r") # получает одну строку текста из сокета до \n


def send_line(sock: socket.socket, text: str) -> None:
    sock.sendall((text + "\n").encode(ENCODING)) # отправляет строку в сокет


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="File client")
    parser.add_argument("--host", default="127.0.0.1", help="IP/host сервера")
    parser.add_argument("--port", type=int, default=9000, help="Порт сервера")
    parser.add_argument(
        "--dir",
        default="client_storage",
        help="Локальная папка клиента для upload/download",
    )
    return parser.parse_args() # считывает параметры запуска программы


def cmd_list(sock: socket.socket) -> None:
    send_line(sock, "LIST")
    response = recv_line(sock)
    if not response.startswith("OK "):
        print(response)
        return

    try:
        count = int(response.split(maxsplit=1)[1])
    except ValueError:
        print("Некорректный ответ сервера")
        return

    if count == 0:
        print("Файлов на сервере нет")
        return

    print("Файлы на сервере:")
    for _ in range(count):
        print(" -", recv_line(sock)) # выполняет команду LIST


def cmd_upload(sock: socket.socket, base_dir: str, user_filename: str) -> None:
    local_path = user_filename
    if not os.path.isabs(local_path):
        local_path = os.path.join(base_dir, user_filename)

    if not os.path.exists(local_path) or not os.path.isfile(local_path):
        print("Локальный файл не найден")
        return

    size = os.path.getsize(local_path)
    if size <= 0:
        print("Нельзя загрузить пустой файл")
        return

    remote_name = os.path.basename(local_path)
    send_line(sock, f"UPLOAD {remote_name}")

    response = recv_line(sock)
    if response != "READY":
        print(response)
        return

    send_line(sock, str(size))
    with open(local_path, "rb") as in_file:
        while True:
            chunk = in_file.read(BUFFER_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)

    print(recv_line(sock)) #


def cmd_download(sock: socket.socket, base_dir: str, user_filename: str) -> None:
    remote_name = os.path.basename(user_filename)
    if not remote_name:
        print("Некорректное имя файла")
        return

    send_line(sock, f"DOWNLOAD {remote_name}")
    response = recv_line(sock)

    if response.startswith("ERROR"):
        print(response)
        return

    if not response.startswith("SIZE "):
        print("Некорректный ответ сервера")
        return

    try:
        size = int(response.split(maxsplit=1)[1])
    except ValueError:
        print("Некорректный размер файла")
        return

    os.makedirs(base_dir, exist_ok=True)
    local_path = os.path.join(base_dir, remote_name)

    send_line(sock, "READY")

    remaining = size
    try:
        with open(local_path, "wb") as out_file:
            while remaining > 0:
                chunk = sock.recv(min(BUFFER_SIZE, remaining))
                if not chunk:
                    raise ServerDisconnected("Обрыв соединения во время скачивания")
                out_file.write(chunk)
                remaining -= len(chunk)
    except Exception:
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except OSError:
                pass
        raise

    print(f"OK Файл сохранен: {local_path}")


def run_client(host: str, port: int, base_dir: str) -> None:
    os.makedirs(base_dir, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        print(f"Подключено к серверу {host}:{port}")
        print("Команды: LIST, UPLOAD <filename>, DOWNLOAD <filename>, EXIT")

        while True:
            try:
                raw = input("ftp> ").strip()
            except (EOFError, KeyboardInterrupt):
                raw = "EXIT"
                print()

            if not raw:
                continue

            parts = raw.split(maxsplit=1)
            command = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""

            try:
                if command == "LIST":
                    cmd_list(sock)
                elif command == "UPLOAD":
                    if not arg:
                        print("Укажите имя файла")
                        continue
                    cmd_upload(sock, base_dir, arg)
                elif command == "DOWNLOAD":
                    if not arg:
                        print("Укажите имя файла")
                        continue
                    cmd_download(sock, base_dir, arg)
                elif command == "EXIT":
                    send_line(sock, "EXIT")
                    try:
                        print(recv_line(sock))
                    except ServerDisconnected:
                        pass
                    print("Соединение завершено")
                    break
                else:
                    print("Неизвестная команда")
            except ServerDisconnected as exc:
                print(f"Ошибка: {exc}")
                break
            except OSError as exc:
                print(f"Сетевая ошибка: {exc}") 
                break # клиент ран


if __name__ == "__main__":
    args = parse_args()
    try:
        run_client(args.host, args.port, args.dir)
    except ConnectionRefusedError:
        print("Не удалось подключиться к серверу")
    except OSError as exc:
        print(f"Ошибка клиента: {exc}")
