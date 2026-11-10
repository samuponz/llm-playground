"""The hand-written chat template must give exactly the text Ollama gives the model.

The expected texts are the four cases checked against Ollama in experiment 004
(docs/experiments/004-chat-template-check.md): same token count in every case.
"""
from template import render

EMPTY_THINK = "<think>\n\n</think>\n\n"


def test_one_message_thinking_off():
    messages = [{"role": "user", "content": "My name is Sam."}]
    assert render(messages, thinking=False) == (
        "<|im_start|>user\nMy name is Sam. /no_think<|im_end|>\n"
        "<|im_start|>assistant\n" + EMPTY_THINK
    )


def test_one_message_thinking_on():
    messages = [{"role": "user", "content": "My name is Sam."}]
    assert render(messages, thinking=True) == (
        "<|im_start|>user\nMy name is Sam. /think<|im_end|>\n"
        "<|im_start|>assistant\n"  # no empty think block: the model writes its own
    )


def test_system_message_goes_first_with_a_blank_line():
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
        {"role": "user", "content": "What is the capital of Italy?"},
    ]
    assert render(messages, thinking=False) == (
        "<|im_start|>system\n\nYou are a helpful assistant. Answer briefly.<|im_end|>\n"
        "<|im_start|>user\nWhat is the capital of Italy? /no_think<|im_end|>\n"
        "<|im_start|>assistant\n" + EMPTY_THINK
    )


def test_earlier_turns_are_pasted_back_and_only_the_last_question_gets_the_switch():
    messages = [
        {"role": "user", "content": "My name is Sam."},
        {"role": "assistant", "content": "Nice to meet you, Sam!"},
        {"role": "user", "content": "What is my name?"},
    ]
    assert render(messages, thinking=False) == (
        "<|im_start|>user\nMy name is Sam.<|im_end|>\n"
        "<|im_start|>assistant\nNice to meet you, Sam!<|im_end|>\n"
        "<|im_start|>user\nWhat is my name? /no_think<|im_end|>\n"
        "<|im_start|>assistant\n" + EMPTY_THINK
    )


def test_two_system_messages_are_joined_into_one_block():
    messages = [
        {"role": "system", "content": "Be brief."},
        {"role": "system", "content": "Answer in Italian."},
        {"role": "user", "content": "Hi"},
    ]
    assert render(messages, thinking=True).startswith(
        "<|im_start|>system\n\nBe brief.\n\nAnswer in Italian.<|im_end|>\n"
    )


def test_a_last_assistant_message_stays_open():
    # The model continues it instead of starting a new answer
    messages = [
        {"role": "user", "content": "Count to three."},
        {"role": "assistant", "content": "One, two,"},
    ]
    assert render(messages, thinking=False).endswith("<|im_start|>assistant\nOne, two,")
