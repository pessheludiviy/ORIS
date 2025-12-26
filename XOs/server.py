import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

clients = []
clients_lock = threading.Lock()
games = {}
games_lock = threading.Lock()
waiting_player = []
waiting_lock = threading.Lock()


def send_message(client, message):
    try:
        client.sendall((message + '\n').encode('utf-8'))
    except (ConnectionResetError, BrokenPipeError):
        print(f"[ОШИБКА] Не удалось отправить сообщение клиенту {client}")


def create_game(player1, player2, player1_name, player2_name):
    board = [[' ' for _ in range(3)] for _ in range(3)]
    game_data = {
        'board': board,
        'turn': 'X',
        'moves_count': 0
    }

    with games_lock:
        games[player1_name] = {
            'opponent': player2_name,
            'symbol': 'X',
            'game': game_data
        }
        games[player2_name] = {
            'opponent': player1_name,
            'symbol': 'O',
            'game': game_data
        }

    send_message(player1, f'BOARD {get_status(game_data)}')
    send_message(player1, f'TURN {game_data["turn"]}')
    send_message(player1, f'OPPONENT {player2_name}')
    send_message(player1, 'SYMBOL X')

    send_message(player2, f'BOARD {get_status(game_data)}')
    send_message(player2, f'TURN {game_data["turn"]}')
    send_message(player2, f'OPPONENT {player1_name}')
    send_message(player2, 'SYMBOL O')

    return game_data


def get_position(position):
    if len(position) != 2:
        return None, None

    row, col = position[0].upper(), position[1]
    if row not in ['A', 'B', 'C'] or col not in ['1', '2', '3']:
        return None, None

    if row == 'A':
        return 0, int(col) - 1
    elif row == 'B':
        return 1, int(col) - 1
    else:
        return 2, int(col) - 1


def check_win(board, player_symbol):
    for row in range(3):
        count = 0
        for col in range(3):
            if board[row][col] == player_symbol:
                count += 1
        if count == 3:
            return True
        count = 0

    for col in range(3):
        count = 0
        for row in range(3):
            if board[row][col] == player_symbol:
                count += 1
        if count == 3:
            return True
        count = 0

    if board[0][0] == player_symbol and board[1][1] == player_symbol and board[2][2] == player_symbol:
        return True
    elif board[0][2] == player_symbol and board[1][1] == player_symbol and board[2][0] == player_symbol:
        return True

    return False


def make_move(game_data, player, position):
    player_symbol = games[player]['symbol']

    if game_data['turn'] != player_symbol:
        return False, 'Не ваш ход'

    row, col = get_position(position)
    if row is None or col is None:
        return False, 'Неверный ход'

    if game_data['board'][row][col] != ' ':
        return False, 'Клетка занята'

    game_data['board'][row][col] = player_symbol
    game_data['moves_count'] += 1

    if check_win(game_data['board'], player_symbol):
        return True, 'WIN'

    if game_data['moves_count'] >= 9:
        return True, "DRAW"

    game_data['turn'] = 'O' if player_symbol == 'X' else 'X'

    return True, 'Continue'


def get_status(game_data):
    moves = []
    rows = ['A', 'B', 'C']
    for row in range(3):
        for col in range(3):
            if game_data['board'][row][col] != ' ':
                moves.append(f"{rows[row]}{col + 1}:{game_data['board'][row][col]}")
    return ','.join(moves)


def broadcast_board(player_name, message, send_himself):
    with games_lock:
        if player_name in games:
            opponent_name = games[player_name]['opponent']

            player_conn = None
            opponent_conn = None

            with clients_lock:
                for client_info in clients:
                    if client_info['name'] == player_name:
                        player_conn = client_info['conn']
                    elif client_info['name'] == opponent_name:
                        opponent_conn = client_info['conn']

            if send_himself and player_conn:
                send_message(player_conn, message)
            if opponent_conn:
                send_message(opponent_conn, message)


def broadcast_chat(player_name, message):
    with games_lock:
        if player_name in games:
            opponent_name = games[player_name]['opponent']

            player_conn = None
            opponent_conn = None

            with clients_lock:
                for client_info in clients:
                    if client_info['name'] == player_name:
                        player_conn = client_info['conn']
                    elif client_info['name'] == opponent_name:
                        opponent_conn = client_info['conn']

            if player_conn:
                send_message(player_conn, message)
            if opponent_conn:
                send_message(opponent_conn, message)


def handle_client(conn, addr):
    print(f"[НОВОЕ ПОДКЛЮЧЕНИЕ] {addr}")
    player_name = f"Player{addr[1]}"
    with clients_lock:
        clients.append({'conn': conn, 'name': player_name, 'addr': addr})
    try:
        with waiting_lock:
            if len(waiting_player) == 0:
                waiting_player.append((conn, player_name))
                send_message(conn, 'OPPONENT Ожидание соперника')
                print(f'[ОЖИДАНИЕ] {addr} в очереди. Ждущих: {len(waiting_player)}')
            else:
                player1_conn, player1_name = waiting_player.pop(0)
                player2_conn, player2_name = conn, player_name

                game_data = create_game(player1_conn, player2_conn, player1_name, player2_name)

                print(f'[ИГРА СОЗДАНА] {player1_name} vs {player2_name}')

        while True:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                print(f"[ОТКЛЮЧЕНИЕ] Клиент {addr} закрыл соединение")
                break

            if data.startswith("MOVE"):
                parts = data.split()
                if len(parts) < 2:
                    send_message(conn, 'ERROR Неверный формат ввода')
                    continue
                position = parts[1].upper()

                if player_name not in games:
                    send_message(conn, 'ERROR Вы не в игре!')
                    continue

                game_data = games[player_name]['game']
                success, res = make_move(game_data, player_name, position)

                if success:
                    board_status = get_status(game_data)
                    broadcast_board(player_name, f"BOARD {board_status}", True)

                    if res == 'WIN':
                        with games_lock:
                            opponent_name = games[player_name]['opponent']

                        winner_conn = None
                        loser_conn = None
                        with clients_lock:
                            for client_info in clients:
                                if client_info['name'] == player_name:
                                    winner_conn = client_info['conn']
                                elif client_info['name'] == opponent_name:
                                    loser_conn = client_info['conn']

                        if winner_conn:
                            send_message(winner_conn, "WIN")
                        if loser_conn:
                            send_message(loser_conn, "LOSE")

                        with games_lock:
                            del games[player_name]
                            del games[opponent_name]
                    elif res == 'DRAW':
                        broadcast_board(player_name, "DRAW", True)
                        with games_lock:
                            opponent_name = games[player_name]['opponent']
                            del games[player_name]
                            del games[opponent_name]
                    else:
                        broadcast_board(player_name, f"TURN {game_data['turn']}", True)
                else:
                    send_message(conn, f'ERROR {res}')

            elif data.startswith("CHAT"):
                message_text = data[5:]
                if message_text:
                    broadcast_chat(player_name, f'CHAT {player_name}: {message_text}')
                else:
                    send_message(conn, "ERROR Пустое сообщение")

            elif data.startswith("STATUS"):
                if player_name in games:
                    game_data = games[player_name]['game']
                    board_status = get_status(game_data)
                    send_message(conn, f"BOARD {board_status}")
                    send_message(conn, f"TURN {game_data['turn']}")
                else:
                    send_message(conn, 'ERROR Вы не в игре')

            elif data.lower() == "exit":
                print(f"[ОТКЛЮЧЕНИЕ] Клиент {addr} вышел из игры")
                break

            else:
                send_message(conn, "ERROR Неизвестная команда")
    except ConnectionResetError:
        print(f"[ОТКЛЮЧЕНИЕ] Клиент {addr} отключился некорректно")
    finally:
        with clients_lock:
            for i, client_info in enumerate(clients):
                if client_info['name'] == player_name:
                    clients.pop(i)
                    break

        with waiting_lock:
            for i, (waiting_conn, waiting_name) in enumerate(waiting_player):
                if waiting_name == player_name:
                    waiting_player.pop(i)
                    print(f'[УДАЛЕН ИЗ ОЖИДАНИЯ] {player_name}')
                    break

        with games_lock:
            if player_name in games:
                opponent_name = games[player_name]['opponent']
                for client_info in clients:
                    if client_info['name'] == opponent_name:
                        send_message(client_info['conn'], "ERROR Соперник отключился")
                        send_message(client_info['conn'], "CHAT Система: Соперник покинул игру")
                        send_message(client_info['conn'], "WIN")
                        break
        del games[player_name]
        if opponent_name in games:
            del games[opponent_name]

    print(f"[КЛИЕНТ УДАЛЕН] {player_name}")
    conn.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    with server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVER RUNNING] {HOST}:{PORT}")
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()


if __name__ == "__main__":
    start_server()