let
  pkgs = import (builtins.fetchTarball {
    name = "nixos-unstable-2024-06-05";
    url = "https://github.com/nixos/nixpkgs/archive/57610d2f8f0937f39dbd72251e9614b1561942d8.tar.gz";
    sha256 = "0k8az8vmfdk1n8xlza252sqk0hm1hfc7g67adin6jxqaab2s34n9";
  }) { };
  poetry2nix = import (builtins.fetchTarball {
    name = "poetry2nix-2024.6.557458";
    url = "https://github.com/nix-community/poetry2nix/archive/81662ae1ad31491eae3bb1d976fb74c71853bc63.tar.gz";
    sha256 = "1zvlhzlc7mxr74qii3mkyn4iyd5rdivrm40yf7r7jvj9ry5gnbx9";
  }) { inherit pkgs; };
  poetryPackages = poetry2nix.mkPoetryPackages {
    projectDir = ./.;
    overrides = poetry2nix.overrides.withDefaults (
      self: super: {
        types-shapely = super.types-shapely.overridePythonAttrs (old: {
          propagatedBuildInputs = old.propagatedBuildInputs or [ ] ++ [ self.setuptools ];
        });
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
    (pkgs.gdal.override { geos = pkgs.geos_3_11; })
    pkgs.gitFull
    pkgs.nixfmt-rfc-style
    pkgs.nodejs
    pkgs.poetry
    pkgs.statix
    pkgs.which
  ];
  shellHook = ''
    ln --force --no-target-directory --symbolic "${pkgs.lib.getExe pythonWithPackages}" python
  '';
}
