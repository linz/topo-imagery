let
  pkgs = import (builtins.fetchTarball {
    name = "nixos-unstable-2024-10-17";
    url = "https://github.com/nixos/nixpkgs/archive/a3c0b3b21515f74fd2665903d4ce6bc4dc81c77c.tar.gz";
    sha256 = "1wn29537l343lb0id0byk0699fj0k07m1n2d7jx2n0ssax55vhwy";
  }) { overlays = [ (_final: prev: { geos = prev.geos_3_11; }) ]; };
  poetry2nix = import (builtins.fetchTarball {
    url = "https://github.com/nix-community/poetry2nix/archive/2024.10.1637698.tar.gz";
    sha256 = "08w14qxgn6rklfc83p8z6h91si854kl6nr1pjhdn8smfx7nw5819";
  }) { inherit pkgs; };
  poetryPackages = poetry2nix.mkPoetryPackages {
    projectDir = ./.;
    python = pkgs.python312;
    overrides = poetry2nix.overrides.withDefaults (
      final: prev: {
        cryptography = prev.cryptography.overridePythonAttrs (
          # TODO: Remove when <URL> is in poetry2nix
          old: {
            nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
              final.distutils
            ];
          }
        );
      }
    );
  };
  pythonWithPackages = poetryPackages.python.withPackages (_ps: poetryPackages.poetryPackages);
in
pkgs.mkShell {
  packages = [
    pythonWithPackages
    pkgs.bashInteractive
    pkgs.cacert
    pkgs.deadnix
    pkgs.gcc # To install Python debugging in IDEA
    pkgs.gdal
    pkgs.gitFull
    pkgs.nixfmt-rfc-style
    pkgs.nodejs
    pkgs.poetry
    pkgs.shellcheck
    pkgs.statix
    pkgs.which
  ];
  shellHook = ''
    ln --force --no-target-directory --symbolic "${pkgs.lib.getExe pythonWithPackages}" python
  '';
}
