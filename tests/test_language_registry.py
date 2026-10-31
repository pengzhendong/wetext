"""Language registration, serialized schemas, and optional pipeline modes."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from wetext import Normalizer, StreamNormalizer, tag
from wetext.cli import main
from wetext.constants import FST_PATHS
from wetext.languages import LANGUAGES, model_names
from wetext.token_parser import TokenParser

NEW = tuple(code for code in LANGUAGES if code not in ("zh", "en", "ja", "ko", "de"))


@pytest.mark.parametrize("lang", LANGUAGES)
def test_registry_models_and_modes(lang):
    pipeline = LANGUAGES[lang]
    for operator in pipeline["directions"]:
        for deterministic, cased in ((True, False), (False, False), (True, True)):
            for name in model_names(lang, operator, deterministic=deterministic, cased=cased):
                assert Path(FST_PATHS[lang][operator][name]).is_file()
    assert pipeline["module"]


@pytest.mark.parametrize("lang,operator", [(lang, op) for lang in NEW for op in LANGUAGES[lang]["directions"]])
def test_cli_stream_mapping_and_schema(lang, operator):
    normalizer = Normalizer(lang=lang, operator=operator)
    source = (
        "23"
        if operator == "tn" or "tn" not in LANGUAGES[lang]["directions"]
        else normalizer.normalize("23", operator="tn")
    )
    output = normalizer.normalize(source)
    result = CliRunner().invoke(main, ["--lang", lang, "--operator", operator, source])
    assert result.exit_code == 0, result.output
    assert result.output == output + "\n"
    assert normalizer.normalize_with_mapping(source).output_text == output
    assert normalizer.normalize(source, nbest=3)[0] == output
    stream = StreamNormalizer(lang=lang, operator=operator)
    for char in source:
        stream.feed(char)
    assert stream.flush() == output
    parser = TokenParser(lang, operator)
    parser.parse(tag(source, lang, operator))
    assert parser.tokens
    for empty in ("", " ", "\t\n"):
        assert normalizer.normalize(empty) == ""
        assert normalizer.normalize(empty, nbest=3) == [""]


def test_spanish_cased_mode():
    assert Normalizer(lang="es", operator="itn").normalize("Doce Dólares") == "Doce Dólares"
    assert Normalizer(lang="es", operator="itn", cased=True).normalize("Doce Dólares") == "$12"
    result = CliRunner().invoke(main, ["--lang", "es", "--operator", "itn", "--cased", "Doce Dólares"])
    assert result.exit_code == 0
    assert result.output == "$12\n"


@pytest.mark.parametrize("lang,text", [("hy", "տասներկու"), ("ar", "اثنا عشر"), ("ru", "двенадцать"), ("hi", "बारह")])
def test_script_detection(lang, text):
    from wetext.utils import get_lang

    assert get_lang(text) == lang
    assert Normalizer(operator="itn").normalize(text) == Normalizer(lang=lang, operator="itn").normalize(text)


@pytest.mark.parametrize("lang", ["hi_en", "es_en"])
def test_itn_only_rejects_tn(lang):
    with pytest.raises(ValueError, match="supports itn only"):
        Normalizer(lang=lang, operator="tn")
    with pytest.raises(ValueError, match="supports itn only"):
        tag("12", lang, "tn")
    result = CliRunner().invoke(main, ["--lang", lang, "--operator", "tn", "12"])
    assert result.exit_code == 2
    assert "supports itn only" in result.output
