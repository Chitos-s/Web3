import argparse
import os
import socket
import threading
from typing import Optional

BUFFER_SIZE = 64 * 1024
ENCODING = "utf-8"


class ClientDisconnected(Exception):
    pass

def recv_line(sock: socket.socket) -> str: 
    
    data = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            if not data:
                raise ClientDisconnected("Client disconnected")
            break
        if chunk == b"\n":
            break
        data.extend(chunk)
    return data.decode(ENCODING, errors="replace").rstrip("\r") # получает одну строку текста из сокета до \n



def send_line(sock: socket.socket, text: str) -> None:
    sock.sendall((text + "\n").encode(ENCODING)) # отправляет строку, добавляя символ новой строки и кодируя её в UTF-8


def safe_filename(raw_name: str) -> Optional[str]:
    
    cleaned = os.path.basename(raw_name.strip())
    if not cleaned:
        return None
    if cleaned in {".", ".."}:
        return None
    return cleaned # проверяет имя файла


def handle_list(sock: socket.socket, storage_dir: str) -> None:
    files = []
    for item in os.listdir(storage_dir):
        full_path = os.path.join(storage_dir, item)
        if os.path.isfile(full_path):
            files.append(item)
    files.sort()

    send_line(sock, f"OK {len(files)}")
    for name in files:
        send_line(sock, name) # обрабатывает команду LIST


def handle_upload(sock: socket.socket, storage_dir: str, filename: str) -> None:
    safe_name = safe_filename(filename)
    if not safe_name:
        send_line(sock, "ERROR Некорректное имя файла")
        return

    send_line(sock, "READY")

    try:
        size_line = recv_line(sock)
        size = int(size_line)
    except ValueError:
        send_line(sock, "ERROR Некорректный размер файла")
        return
    except ClientDisconnected:
        raise

    if size <= 0:
        send_line(sock, "ERROR Нельзя загрузить пустой файл")
        return

    target_path = os.path.join(storage_dir, safe_name)
    try:
        remaining = size
        with open(target_path, "wb") as out_file:
            while remaining > 0:
                chunk = sock.recv(min(BUFFER_SIZE, remaining))
                if not chunk:
                    raise ClientDisconnected("Client disconnected during upload")
                out_file.write(chunk)
                remaining -= len(chunk)
    except Exception:
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except OSError:
                pass
        raise

    send_line(sock, f"OK Файл {safe_name} загружен") # аплодит файлы на сервер


def handle_download(sock: socket.socket, storage_dir: str, filename: str) -> None:
    safe_name = safe_filename(filename)
    if not safe_name:
        send_line(sock, "ERROR Некорректное имя файла")
        return

    source_path = os.path.join(storage_dir, safe_name)
    if not os.path.exists(source_path) or not os.path.isfile(source_path):
        send_line(sock, "ERROR Файл не найден")
        return

    size = os.path.getsize(source_path)
    send_line(sock, f"SIZE {size}")

    client_state = recv_line(sock)
    if client_state != "READY":
        send_line(sock, "ERROR Клиент не готов к получению")
        return

    with open(source_path, "rb") as in_file:
        while True:
            chunk = in_file.read(BUFFER_SIZE)
            if not chunk:
                break
            sock.sendall(chunk) # даунлодит файлы с сервера


def handle_client(client_sock: socket.socket, client_addr, storage_dir: str) -> None:
    print(f"[+] Клиент подключен: {client_addr}")
    try:
        while True:
            try:
                line = recv_line(client_sock)
            except ClientDisconnected:
                print(f"[-] Клиент отключился: {client_addr}")
                break

            if not line:
                send_line(client_sock, "ERROR Пустая команда")
                continue

            parts = line.split(maxsplit=1)
            command = parts[0].upper()
            argument = parts[1] if len(parts) > 1 else ""

            try:
                if command == "LIST":
                    handle_list(client_sock, storage_dir)
                elif command == "UPLOAD":
                    if not argument:
                        send_line(client_sock, "ERROR Укажите имя файла")
                        continue
                    handle_upload(client_sock, storage_dir, argument)
                elif command == "DOWNLOAD":
                    if not argument:
                        send_line(client_sock, "ERROR Укажите имя файла")
                        continue
                    handle_download(client_sock, storage_dir, argument)
                elif command == "EXIT":
                    send_line(client_sock, "BYE")
                    print(f"[i] Клиент завершил сессию: {client_addr}")
                    break
                else:
                    send_line(client_sock, "ERROR Неизвестная команда")
            except ClientDisconnected:
                print(f"[-] Обрыв соединения с клиентом: {client_addr}")
                break
            except Exception as exc:
                print(f"[!] Ошибка при обработке клиента {client_addr}: {exc}")
                send_line(client_sock, "ERROR Внутренняя ошибка сервера")
    finally:
        try:
            client_sock.close()
        except OSError:
            pass # главная функция обработки клиента


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="File server")
    parser.add_argument("--host", default="0.0.0.0", help="IP/host для прослушивания")
    parser.add_argument("--port", type=int, default=9000, help="Порт сервера")
    parser.add_argument(
        "--storage",
        default="server_storage",
        help="Директория хранения файлов на сервере",
    )
    return parser.parse_args() # считывание параметров командной строки


def run_server(host: str, port: int, storage_dir: str) -> None:
    os.makedirs(storage_dir, exist_ok=True)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()

    print(f"[i] Сервер запущен: {host}:{port}")
    print(f"[i] Директория хранения: {os.path.abspath(storage_dir)}")

    try:
        while True:
            try:
                client_sock, client_addr = server_sock.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, client_addr, storage_dir),
                    daemon=True,
                )
                thread.start()
            except Exception as exc:
                print(f"[!] Ошибка accept: {exc}")
    except KeyboardInterrupt:
        print("\n[i] Остановка сервера...")
    finally:
        server_sock.close() # сервер бегит 


if __name__ == "__main__":
    args = parse_args()
    run_server(args.host, args.port, args.storage)
