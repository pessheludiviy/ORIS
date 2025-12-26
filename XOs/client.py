import socket
import threading
import re

HOST = '127.0.0.1'
PORT = 12345

class GameState:
    def __init__(self):
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_turn = 'X'
        self.my_symbol = ' '
        self.opponent = "Ожидание соперника"
        self.chat_messages = []
        self.game_over = False
        self.lock = threading.Lock()
        self.last_command = None

def draw_board(game_state):
    with game_state.lock:
        print('\n' + '╔═══════════════════╗')
        print('║  КРЕСТИКИ-НОЛИКИ  ║')
        print('╠═══════════════════╣')
        print('║     1   2   3     ║')
        print('║   ┌───┬───┬───┐   ║')
        rows = ['A', 'B', 'C']
        for i in range(3):
            print(f'║ {rows[i]} │ {game_state.board[i][0]} │ {game_state.board[i][1]} │ {game_state.board[i][2]} │   ║')
            if i < 2:
                print('║   ├───┼───┼───┤   ║')
        print('║   └───┴───┴───┘   ║')
        print('╚═══════════════════╝')

        print(f'Ход: {game_state.current_turn}')
        print(f"Соперник: {game_state.opponent}")
        print(f'Чат: {game_state.chat_messages[-1] if game_state.chat_messages else "нет сообщений"}')
        print('Введите команду: ___')

def update_board(game_state, data):
    with game_state.lock:
        game_state.board = [[' ' for _ in range(3)] for _ in range(3)]
        if not data.strip():
            return
        moves = data.split(',')
        for move in moves:
            if ':' in move:
                pos, player = move.split(':')
                if len(pos) == 2:
                    col = int(pos[1]) - 1
                    row_map = {'A': 0, 'B': 1, 'C': 2}
                    if pos[0].upper() in row_map and 0 <= col <= 2:
                        game_state.board[row_map[pos[0].upper()]][col] = player

def turn(move):
    return re.match(r'^[A-Ca-c][1-3]$', move)

def receive_messages(sock, game_state):
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("[ОТКЛЮЧЕНИЕ] Сервер закрыл соединение")
                break

            lines = data.split('\n')
            should_draw = False

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('BOARD'):
                    if game_state.last_command and game_state.last_command.upper() == "STATUS":
                        print(line)
                        continue
                    update_board(game_state, line[6:])

                elif line.startswith('TURN'):
                    if game_state.last_command and game_state.last_command.upper() == "STATUS":
                        print(line)
                        game_state.last_command = None
                        continue
                    with game_state.lock:
                        game_state.current_turn = line[5:]
                    should_draw = True

                elif line.startswith('SYMBOL'):
                    with game_state.lock:
                        game_state.my_symbol = line[6:]
                    print(f'\n[ИНФО] Ваш символ: {game_state.my_symbol}')

                elif line.startswith('CHAT'):
                    chat_msg = line[5:]
                    with game_state.lock:
                        game_state.chat_messages.append(chat_msg)
                        if len(game_state.chat_messages) > 3:
                            game_state.chat_messages.pop(0)
                    print(f'\n[ЧАТ]: {chat_msg}')
                    should_draw = True

                elif line.startswith('WIN'):
                    with game_state.lock:
                        if not game_state.game_over:
                            game_state.game_over = True
                            print('\n[ИНФО] Победа! Вы выиграли!')
                    should_draw = True

                elif line.startswith('LOSE'):
                    with game_state.lock:
                        if not game_state.game_over:
                            game_state.game_over = True
                            print('\n[ИНФО] Поражение. Попробуйте снова.')
                    should_draw = True

                elif line.startswith('DRAW'):
                    with game_state.lock:
                        if not game_state.game_over:
                            game_state.game_over = True
                            print('\n[ИНФО] Ничья!')
                    should_draw = True

                elif line.startswith('OPPONENT'):
                    with game_state.lock:
                        game_state.opponent = line[9:]
                    print(f'\n[ИНФО] Ваш соперник: {game_state.opponent}')
                    should_draw = True

                elif line.startswith('ERROR'):
                    print(f'\n[ОШИБКА]: {line[6:]}')

            if should_draw:
                draw_board(game_state)

        except ConnectionResetError:
            print("[ОТКЛЮЧЕНИЕ] Соединение разорвано сервером")
            break
        except Exception as e:
            print(f'[ОШИБКА receive_messages]: {e}')
            break

def start_client():
    game_state = GameState()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with client_socket:
        client_socket.connect((HOST, PORT))
        print("[ПОДКЛЮЧЕНИЕ] Подключено к серверу")

        receive_thread = threading.Thread(target=receive_messages, args=(client_socket, game_state), daemon=True)
        receive_thread.start()

        while True:
            try:
                command = input().strip()
                game_state.last_command = command

                if command.lower() == "exit":
                    client_socket.sendall("exit\n".encode('utf-8'))
                    print("[ВЫХОД] Вы отключились от сервера")
                    break

                elif command.upper().startswith('MOVE '):
                    with game_state.lock:
                        if game_state.game_over:
                            print('[ОШИБКА] Игра окончена. Перезапустите клиент.')
                            continue
                    move = command[5:].upper()
                    if turn(move):
                        client_socket.sendall(f'MOVE {move}\n'.encode('utf-8'))
                    else:
                        print('[ОШИБКА] Неверный формат хода. Используйте A1, B2, C3 и т.д.')

                elif command.upper().startswith('CHAT '):
                    client_socket.sendall(f'{command}\n'.encode('utf-8'))

                elif command.upper() == 'STATUS':
                    client_socket.sendall("STATUS\n".encode('utf-8'))

                else:
                    print('[ОШИБКА] Неизвестная команда')

            except KeyboardInterrupt:
                print("\n[ВЫХОД] Завершение работы...")
                client_socket.sendall("exit\n".encode('utf-8'))
                break
            except Exception as e:
                print(f'[ОШИБКА input_loop]: {e}')

if __name__ == "__main__":
    start_client()