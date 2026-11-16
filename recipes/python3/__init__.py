from os.path import join

from pythonforandroid.recipes.python3 import Python3Recipe


class FixedPython3Recipe(Python3Recipe):
    """Python 3.11 + современный clang: разрешаем неявные объявления в grp."""

    def get_recipe_dir(self):
        # Патчи берём из основного reцепта p4a, а не из локальной папки.
        return join(self.ctx.root_dir, "recipes", self.name)

    def get_recipe_env(self, arch=None, with_flags_in_cc=True):
        env = super().get_recipe_env(arch, with_flags_in_cc)
        env["CFLAGS"] += (
            " -Wno-implicit-function-declaration"
            " -Wno-error=implicit-function-declaration"
            " -Wno-int-conversion"
        )
        return env


recipe = FixedPython3Recipe()
