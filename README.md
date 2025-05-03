A fresh take on chess puzzle managment for coaches.

# mintmate_config.toml README

This README explains how to configure `mintmate_config.toml` for the puzzle-export script.

## Overview
The `mintmate_config.toml` file specifies:
- Where to find your Lichess puzzles CSV (`csv_path`)
- Where to save outputs (`output_dir`)
- Which board and piece style to use (`board_theme`, `piece_style`)
- Which puzzle batches to generate (`[[puzzles]]` sections)

## Top-Level Fields

| Key           | Type   | Description                                                                                  |
|---------------|--------|----------------------------------------------------------------------------------------------|
| `csv_path`    | string | Path to the input CSV of all Lichess puzzles.                                               |
| `output_dir`  | string | Directory where screenshots and XLSX files will be written.                                 |
| `board_theme` | string | Lichess board theme identifier (e.g. `"blue"`, `"wood"`).                                   |
| `piece_style` | string | Lichess piece style identifier (e.g. `"merida"`, `"alpha"`).                                |

## `[[puzzles]]` Array

Each `[[puzzles]]` section defines a batch of puzzles:
1. Filter by theme (case-insensitive substring match on the CSV’s `Themes` column).  
2. Filter by rating range (`min_rating` ≤ puzzle.Rating ≤ `max_rating`).  
3. Randomly select `count` puzzles.

| Key          | Type   | Description                                                                      |
|--------------|--------|----------------------------------------------------------------------------------|
| `type`       | string | Lichess internal theme-ID to filter by (see below for valid values).            |
| `min_rating` | int    | Minimum puzzle rating (inclusive).                                              |
| `max_rating` | int    | Maximum puzzle rating (inclusive).                                              |
| `count`      | int    | Number of puzzles to sample for this theme.                                      |

### Example

```toml
[[puzzles]]
type       = "fork"
min_rating = 1000
max_rating = 1800
count      = 10
```

## Available `type` Values (internal theme-IDs)

These are the exact IDs from Lichess’s `puzzleTheme.xml` and the CSV’s `Themes` column.

### Game Phase
```
opening, middlegame, endgame
```

### Endgame Subtypes
```
rookEndgame, bishopEndgame, pawnEndgame,
knightEndgame, queenEndgame, queenRookEndgame
```

### Basic Motifs
```
advancedPawn, attackingF2F7, capturingDefender,
discoveredAttack, doubleCheck, exposedKing,
fork, hangingPiece, kingsideAttack, pin,
queensideAttack, sacrifice, skewer
```

### Advanced Motifs
```
attraction, clearance, defensiveMove,
deflection, interference, intermezzo, quietMove
```

### Mates
```
mateIn1, mateIn2, mateIn3, mateIn4, mateIn5,
anastasiaMate, arabianMate, backRankMate,
bodenMate, doubleBishopMate, dovetailMate,
hookMate, killBoxMate, smotheredMate, vukovicMate
```

### Special Moves
```
castling, promotion
```

### Goals
```
equality, advantage, crushing
```

### Puzzle Lengths
```
oneMove, short, long
```

### Game Sources
```
master, masterVsMaster, superGM
```

Copy any one of these strings (case-insensitive) into your `type` field to filter your CSV by that theme.

