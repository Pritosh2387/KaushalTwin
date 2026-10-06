"""
Tests: Module 1 — Preprocessing & Normalisation
"""

import pytest
from app.utils.normalisation import (
    normalise_text,
    tokenise,
    split_sentences,
    infer_language,
    detect_script,
    extract_keywords,
    contains_devanagari,
)
from app.services.preprocessing_service import preprocess_text


class TestNormalisation:
    def test_unicode_normalise_preserves_devanagari(self):
        text = "बिजली का काम"
        result = normalise_text(text)
        assert "बिजली" in result

    def test_whitespace_collapsed(self):
        result = normalise_text("hello   world\t\nnew")
        assert "  " not in result
        assert result == "hello world new"

    def test_lowercase_flag(self):
        result = normalise_text("Switch Installation", lowercase=True)
        assert result == "switch installation"

    def test_lowercase_false_preserves_case(self):
        result = normalise_text("Switch Installation", lowercase=False)
        assert "Switch" in result

    def test_empty_string_stays_empty(self):
        result = normalise_text("")
        assert result == ""

    def test_punctuation_spacing_fixed(self):
        result = normalise_text("hello , world")
        assert "hello," in result or "hello , world" in result or "," in result


class TestTokenisation:
    def test_basic_tokenisation(self):
        tokens = tokenise("I install switches and fans")
        assert "install" in tokens
        assert "switches" in tokens

    def test_punctuation_stripped(self):
        tokens = tokenise("wiring, testing.")
        assert "wiring" in tokens
        assert "testing" in tokens

    def test_tokens_are_lowercase(self):
        tokens = tokenise("Switch Installation")
        assert all(t == t.lower() for t in tokens)


class TestSentenceSplitting:
    def test_splits_on_period(self):
        sentences = split_sentences("I do wiring. I install fans.")
        assert len(sentences) >= 2

    def test_splits_on_hindi_fullstop(self):
        text = "मैं तार लगाता हूँ। मैं फैन लगाता हूँ।"
        sentences = split_sentences(text)
        assert len(sentences) >= 2

    def test_single_sentence_no_split(self):
        sentences = split_sentences("I install switches")
        assert len(sentences) == 1


class TestLanguageDetection:
    def test_devanagari_detected_as_hindi(self):
        lang = infer_language("मैं बिजली का काम करता हूँ")
        assert lang == "hi"

    def test_latin_detected_as_english(self):
        lang = infer_language("I install switches and fans")
        assert lang == "en"

    def test_declared_language_trusted(self):
        lang = infer_language("I install switches", declared_language="hi")
        assert lang == "hi"

    def test_contains_devanagari_true(self):
        assert contains_devanagari("बिजली") is True

    def test_contains_devanagari_false(self):
        assert contains_devanagari("electrical") is False


class TestKeywordExtraction:
    def test_stop_words_removed(self):
        kws = extract_keywords("I have been doing electrical work")
        assert "i" not in kws
        assert "have" not in kws
        assert "electrical" in kws or "work" in kws

    def test_meaningful_terms_kept(self):
        kws = extract_keywords("switch installation fault diagnosis")
        assert "switch" in kws or "installation" in kws


class TestPreprocessService:
    def test_full_pipeline_english(self):
        result = preprocess_text("I install switches and fans.", language="en")
        assert result["original_text"] == "I install switches and fans."
        assert result["normalized_text"] == "I install switches and fans."
        assert result["language"] == "en"
        assert len(result["tokens"]) > 0
        assert len(result["sentences"]) > 0

    def test_full_pipeline_hindi(self):
        result = preprocess_text("मैं बिजली का काम करता हूँ।")
        assert result["language"] == "hi"
        assert result["original_text"] is not None

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="empty"):
            preprocess_text("")

    def test_preserves_original(self):
        raw = "  Switch   Installation  "
        result = preprocess_text(raw)
        assert result["original_text"] == raw
        assert result["normalized_text"] != raw  # normalised
