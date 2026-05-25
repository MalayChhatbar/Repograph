class Repograph < Formula
  include Language::Python::Virtualenv

  desc "Local-first code intelligence CLI/TUI for indexing repositories into a dependency graph"
  homepage "https://github.com/MalayChhatbar/repograph"
  url "https://files.pythonhosted.org/packages/source/r/repograph/repograph-0.1.0.tar.gz"
  sha256 "REPLACE_WITH_SOURCE_TARBALL_SHA256"
  license "MIT"

  depends_on "python@3.13"

  # Generate the resource blocks from the published PyPI package with:
  #
  #   brew install brew-pypi-poet
  #   poet -f repograph
  #
  # Replace this comment with the generated resource blocks before publishing
  # the tap. RepoGraph is Python-based, so the tap should be built from the
  # source tarball plus generated Python dependency resources.

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "RepoGraph code intelligence engine", shell_output("#{bin}/repograph --help")
  end
end
