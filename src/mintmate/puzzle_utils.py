import chess
from typing import List

def get_solution_san(original_fen: str, uci_moves: str) -> List[str]:
    """
    Convert UCI moves to SAN and discard setup move.
    """
    board = chess.Board(original_fen)
    moves = uci_moves.split()
    if moves:
        # discard opponent setup
        board.push(chess.Move.from_uci(moves[0]))
    san_list = []
    for u in moves[1:]:
        move = chess.Move.from_uci(u)
        san_list.append(board.san(move))
        board.push(move)
    return san_list

def get_to_move_color(original_fen: str, uci_moves: str) -> str:
    """
    Determine whose turn after discarding setup move.
    """
    board = chess.Board(original_fen)
    moves = uci_moves.split()
    if moves:
        board.push(chess.Move.from_uci(moves[0]))
    return "White" if board.turn else "Black"