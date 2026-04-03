from manimator.audio.voiceover import prepare_text_for_tts


def test_prepare_text_for_tts_replaces_pause():
    assert "pause" not in prepare_text_for_tts("Hello [pause] world").lower()
    assert "..." in prepare_text_for_tts("Hello [pause] world")


def test_prepare_text_for_tts_collapses_whitespace():
    assert prepare_text_for_tts("  a  \n  b  ") == "a b"
