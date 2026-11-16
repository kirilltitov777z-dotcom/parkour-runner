# -*- coding: utf-8 -*-
"""Точка входа игры PARKOUR RUNNER."""
import sys

from game import Game


def main():
    g = Game()
    g.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        try:
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass
        traceback.print_exc()
        sys.exit(1)
