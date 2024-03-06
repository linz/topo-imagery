let
  pkgs = import (
    builtins.fetchTarball {
      url = "https://github.com/nixos/nixpkgs/archive/b06025f1533a1e07b6db3e75151caa155d1c7eb3.tar.gz";
      sha256 = "1b8dim6xpcg3wyb0xa0w4h4m22npbzl2np822x4r7wiw5wnnzg5a";
    }
  ) {};
  poetry2nix =
    import (
      builtins.fetchTarball {
        url = "https://github.com/nix-community/poetry2nix/archive/7df29134065172f24385177ea69e755cb90f196c.tar.gz";
        sha256 = "0qx2iv57vhgraaqj4dm9zd3dha1p6ch4n07pja0hsxsymjbvdanw";
      }
    ) {
      inherit pkgs;
    };
  poetryPackages = poetry2nix.mkPoetryPackages {
    projectDir = builtins.path {
      path = ./.;
      name = "topo-imagery";
    };
    python = pkgs.python310;
    overrides = poetry2nix.overrides.withDefaults (
      final: prev: {
        gitlint = prev.gitlint.override {
          preferWheel = true;
        };
      }
    );
  };
  pythonWithPackages = poetryPackages.python.withPackages (ps: poetryPackages.poetryPackages);
in
  pkgs.mkShell {
    packages = [
      pythonWithPackages
      pkgs.alejandra
      pkgs.awscli2
      pkgs.bashInteractive
      pkgs.cacert
      pkgs.exiftool
      pkgs.gdal
      pkgs.gitFull
      pkgs.poetry
      pkgs.qgis
    ];
    shellHook = ''
      ln --force --no-target-directory --symbolic "${pythonWithPackages}" .venv
    '';
  }
