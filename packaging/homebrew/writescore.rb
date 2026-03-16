# Homebrew formula for WriteScore
# To use: brew tap bohica-labs/writescore && brew install writescore

class Writescore < Formula
  include Language::Python::Virtualenv

  desc "AI writing pattern analysis and scoring tool"
  homepage "https://github.com/BOHICA-LABS/writescore"
  url "https://files.pythonhosted.org/packages/source/w/writescore/writescore-6.4.0.tar.gz"
  sha256 "118ebd7ff109790b427d7e3fe5a04fb41291a4ac927fe6a9cbe5ca29f766e4ea"
  license "MIT"

  depends_on "python@3.12"

  # Core dependencies - these are the main packages
  # Note: Full dependency tree is resolved by pip during installation

  def install
    virtualenv_install_with_resources

    # Download spaCy model post-install
    system libexec/"bin/python", "-m", "spacy", "download", "en_core_web_sm"
  end

  def caveats
    <<~EOS
      WriteScore has been installed with its required spaCy language model.

      First run will download transformer models (~500MB) and cache them.
      Subsequent runs will be much faster.

      Usage:
        writescore analyze document.md
        writescore analyze document.md --detailed
        writescore --help
    EOS
  end

  test do
    # Basic smoke test
    assert_match "WriteScore", shell_output("#{bin}/writescore --version")
  end
end
