let
  pkgs = import (
    builtins.fetchTarball {
      url = "https://github.com/nixos/nixpkgs/archive/7541ec60b6f2d38b76e057135bb5942b78d3370c.tar.gz";
      sha256 = "1ndqfddqmfzd8lfq439kwbpm70qdblkdsw22qd16ibns8kq215cz";
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
