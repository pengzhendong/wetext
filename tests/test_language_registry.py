"""Language registration, serialized schemas, and optional pipeline modes."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from wetext import Normalizer, StreamNormalizer, tag
from wetext.cli import main
from wetext.constants import FST_PATHS
from wetext.languages import LANGUAGES, model_names
from wetext.token_parser import TokenParser

NEW = ("hy", "ar", "fr", "pt", "vi", "ru", "sv", "es", "hi")


@pytest.mark.parametrize("lang", LANGUAGES)
def test_registry_models_and_modes(lang):
    pipeline = LANGUAGES[lang]
    for operator in ("tn", "itn"):
        for deterministic, cased in ((True, False), (False, False), (True, True)):
            for name in model_names(lang, operator, deterministic=deterministic, cased=cased):
                assert Path(FST_PATHS[lang][operator][name]).is_file()
    assert pipeline["module"]


@pytest.mark.parametrize("lang", NEW)
@pytest.mark.parametrize("operator", ["tn", "itn"])
def test_cli_stream_mapping_and_schema(lang, operator):
    normalizer = Normalizer(lang=lang, operator=operator)
    source = "23" if operator == "tn" else normalizer.normalize("23", operator="tn")
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
